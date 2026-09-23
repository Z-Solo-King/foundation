from types import SimpleNamespace
import hashlib

import pytest

import worker


class Request:
    def __init__(self, method, url, payload=None, headers=None):
        self.method = method
        self.url = url
        self._payload = payload
        self.headers = headers or {}

    async def json(self):
        return self._payload


class DB:
    def __init__(self, rows=None, run=None):
        self.rows = rows or []
        self.run = run

    def prepare(self, sql):
        if "artifact_ref" in sql:
            return Statement(self.rows)
        if "SELECT 1 AS ok" in sql:
            return Statement({"ok": 1})
        if "sqlite_master" in sql:
            return Statement(self.rows)
        return Statement(self.run)


class DiagnosticDB:
    def prepare(self, sql):
        if "SELECT 1 AS ok" in sql:
            return Statement({"ok": 1})
        return Statement({"run_id": "diag-run"})


class WrongD1DB:
    def prepare(self, sql):
        return Statement({"ok": 0}) if "SELECT 1 AS ok" in sql else Statement({"run_id": "diag-run"})


class BrokenDiagnosticDB:
    def prepare(self, sql):
        raise RuntimeError("d1 unavailable")


class Statement:
    def __init__(self, value):
        self.value = value

    def bind(self, *args):
        return self

    async def first(self):
        return self.value

    async def all(self):
        return SimpleNamespace(results=self.value or [])

    async def run(self):
        return {"meta": {"changes": 1}}


class BrokenDB:
    def prepare(self, sql):
        raise RuntimeError("d1 unavailable")


class Persistence:
    def __init__(self, env):
        self.env = env

    async def get_artifact(self, key):
        if key == "missing":
            return None
        return b"abc"

    async def create_run(self, run_id, request):
        return run_id

    async def create_run_idempotent(self, request, idempotency_key):
        return "run-idempotent"


class DiagnosticPersistence:
    def __init__(self, env):
        self.env = env
        self.artifacts = {}
        self.runs = {}

    async def create_run(self, run_id, request):
        self.runs[run_id] = {"run_id": run_id}
        return run_id

    async def get_run(self, run_id):
        return self.runs.get(run_id)

    async def put_artifact(self, key, content, content_type="application/octet-stream"):
        self.artifacts[key] = bytes(content)
        return {"key": key, "sha256": hashlib.sha256(content).hexdigest(), "size": len(content)}

    async def get_artifact(self, key):
        return self.artifacts.get(key)

    async def delete_artifact(self, key):
        self.artifacts.pop(key, None)


class BrokenDiagnosticPersistence(DiagnosticPersistence):
    async def put_artifact(self, key, content, content_type="application/octet-stream"):
        raise RuntimeError("b2 unavailable")


class BrokenReadPersistence(DiagnosticPersistence):
    async def get_artifact(self, key):
        raise RuntimeError("b2 read unavailable")


class BrokenDeletePersistence(DiagnosticPersistence):
    async def delete_artifact(self, key):
        raise RuntimeError("b2 delete unavailable")


class BrokenPersistence(Persistence):
    async def create_run(self, run_id, request):
        raise RuntimeError("persistence down")

    async def create_run_idempotent(self, request, idempotency_key):
        raise RuntimeError("idempotency down")


@pytest.mark.asyncio
async def test_public_infrastructure_verify_success(monkeypatch):
    monkeypatch.setattr(worker, "CloudflarePersistence", DiagnosticPersistence)
    body, status = await worker._public_infrastructure_verify(SimpleNamespace(DB=DiagnosticDB()))
    assert status == 200
    assert body["ok"] is True
    assert {check["name"] for check in body["checks"]} == {"cloudflare_d1", "backblaze_b2_lifecycle"}


@pytest.mark.asyncio
async def test_public_infrastructure_verify_fail_closed(monkeypatch):
    monkeypatch.setattr(worker, "CloudflarePersistence", BrokenDiagnosticPersistence)
    body, status = await worker._public_infrastructure_verify(SimpleNamespace(DB=BrokenDiagnosticDB()))
    assert status == 503
    assert body["ok"] is False
    assert any(check["name"] == "cloudflare_d1" and check["ok"] is False for check in body["checks"])


@pytest.mark.asyncio
async def test_public_infrastructure_verify_rejects_bad_d1(monkeypatch):
    monkeypatch.setattr(worker, "CloudflarePersistence", DiagnosticPersistence)
    body, status = await worker._public_infrastructure_verify(SimpleNamespace(DB=WrongD1DB()))
    assert status == 503
    assert body["ok"] is False
    assert any(check["name"] == "cloudflare_d1" and check["ok"] is False for check in body["checks"])


@pytest.mark.asyncio
async def test_public_infrastructure_verify_b2_failure_paths(monkeypatch):
    monkeypatch.setattr(worker, "CloudflarePersistence", BrokenReadPersistence)
    body, status = await worker._public_infrastructure_verify(SimpleNamespace(DB=DiagnosticDB()))
    assert status == 503
    assert any(check["name"] == "backblaze_b2_lifecycle" and check["ok"] is False for check in body["checks"])
    monkeypatch.setattr(worker, "CloudflarePersistence", BrokenDeletePersistence)
    body, status = await worker._public_infrastructure_verify(SimpleNamespace(DB=DiagnosticDB()))
    assert status == 503
    assert any(check["name"] == "backblaze_b2_lifecycle" and check["ok"] is False for check in body["checks"])


@pytest.mark.asyncio
async def test_readiness_payload_public_d1_paths():
    ready, status = await worker._readiness_payload(SimpleNamespace(DB=DB()))
    assert status == 200
    assert ready["database"] is True
    not_ready, status = await worker._readiness_payload(SimpleNamespace(DB=WrongD1DB()))
    assert status == 503
    assert not_ready["database"] is False
    not_ready, status = await worker._readiness_payload(SimpleNamespace(DB=BrokenDiagnosticDB()))
    assert status == 503
    assert not_ready["database"] is False


@pytest.mark.asyncio
async def test_storage_diagnostic_verifies_round_trip_and_missing_artifacts(monkeypatch):
    monkeypatch.setattr(worker, "CloudflarePersistence", Persistence)
    rows = [
        {"artifact_ref": "good", "content_hash": "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad", "content_length": 3},
        {"artifact_ref": "missing", "content_hash": "x", "content_length": 1},
    ]
    body, status = await worker._storage_diagnostic(SimpleNamespace(DB=DB(rows=rows)), "run-1")
    assert status == 503
    assert body["ok"] is False
    assert body["artifacts"][0]["actual_bytes"] == 3
    assert body["artifacts"][1]["error"] == "artifact not found"
    good_rows = [{"artifact_ref": "good", "content_hash": "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad", "content_length": 3}]
    body, status = await worker._storage_diagnostic(SimpleNamespace(DB=DB(rows=good_rows)), "run-2")
    assert status == 200 and body["ok"] is True


@pytest.mark.asyncio
async def test_worker_http_public_diagnostics_and_research_fail_closed_paths(monkeypatch):
    monkeypatch.setattr(worker, "CloudflarePersistence", Persistence)
    env = SimpleNamespace(DB=DB(rows=[]), ENVIRONMENT="production", AUTH_TOKEN="secret")
    entry = worker.Default(); entry.env = env
    unauthorized = await entry.fetch(Request("POST", "https://x/api/v1/chatbot/diagnostic", [], {}))
    assert "unauthorized" in str(unauthorized)
    auth_headers = {"Authorization": "Bearer secret", "Content-Type": "application/json"}
    public_invalid = await entry.fetch(Request("POST", "https://x/api/v1/chatbot/diagnostic", [], auth_headers))
    assert "invalid JSON object" in str(public_invalid)
    unsupported = await entry.fetch(Request("POST", "https://x/api/v1/chatbot/diagnostic", {"operation": "knowledge"}, auth_headers))
    assert "unsupported public diagnostic operation" in str(unsupported)
    public_test = await entry.fetch(Request("POST", "https://x/api/v1/chatbot/diagnostic", {"operation": "infrastructure_verify_public_test"}, auth_headers))
    assert "checks" in str(public_test)
    storage_unauthorized = await entry.fetch(Request("POST", "https://x/api/v1/storage/diagnostic", {"run_id": "run-1"}, {"Authorization": "Bearer bad", "Content-Type": "application/json"}))
    assert "unauthorized" in str(storage_unauthorized)
    no_run = await entry.fetch(Request("POST", "https://x/api/v1/storage/diagnostic", {}, auth_headers))
    assert "run_id" in str(no_run)
    storage = await entry.fetch(Request("POST", "https://x/api/v1/storage/diagnostic", {"run_id": "run-1"}, auth_headers))
    assert "artifacts" in str(storage)
    async def broken_storage(*args, **kwargs): raise RuntimeError("storage diagnostic exploded")
    monkeypatch.setattr(worker, "_storage_diagnostic", broken_storage)
    failed_storage = await entry.fetch(Request("POST", "https://x/api/v1/storage/diagnostic", {"run_id": "run-1"}, auth_headers))
    assert "storage diagnostic failure" in str(failed_storage)
    missing = await entry.fetch(Request("GET", "https://x/api/v1/research/missing", None, {"Authorization": "Bearer secret"}))
    assert "run not found" in str(missing)
    persistence_error = worker.Default(); persistence_error.env = SimpleNamespace(DB=BrokenDB(), ENVIRONMENT="production", AUTH_TOKEN="secret")
    failed_get = await persistence_error.fetch(Request("GET", "https://x/api/v1/research/run-1", None, {"Authorization": "Bearer secret"}))
    assert "persistence failure" in str(failed_get)
    invalid_research = await entry.fetch(Request("POST", "https://x/api/v1/research", [], auth_headers))
    assert "invalid JSON object" in str(invalid_research)
    bad_shape = await entry.fetch(Request("POST", "https://x/api/v1/research", {"question": "x", "unexpected": True}, auth_headers))
    assert "unexpected" in str(bad_shape)
    rejected = await entry.fetch(Request("POST", "https://x/api/v1/research", {"question": "x", "strict_zero_cost_only": False}, auth_headers))
    assert "strict $0 cost mode" in str(rejected)


@pytest.mark.asyncio
async def test_research_persistence_failures_and_idempotency(monkeypatch):
    monkeypatch.setattr(worker, "CloudflarePersistence", BrokenPersistence)
    entry = worker.Default(); entry.env = SimpleNamespace(DB=DB(), ENVIRONMENT="production", AUTH_TOKEN="secret")
    request = Request("POST", "https://x/api/v1/research", {"question": "x", "source_urls": [], "strict_zero_cost_only": True}, {"Authorization": "Bearer secret", "Content-Type": "application/json"})
    failed = await entry.fetch(request)
    assert "execution/persistence failure" in str(failed)
    assert '"phase": "create_run"' in str(failed)
    assert '"error_class": "RuntimeError"' in str(failed)
    request.headers["Idempotency-Key"] = "key-1"
    failed_idempotent = await entry.fetch(request)
    assert "execution/persistence failure" in str(failed_idempotent)
    assert '"phase": "create_run"' in str(failed_idempotent)


@pytest.mark.asyncio
async def test_health_payload_uses_worker_environment_binding():
    payload = await worker._health_payload(SimpleNamespace(ENVIRONMENT="production"))
    assert payload["environment"] == "production"


@pytest.mark.asyncio
async def test_health_payload_preserves_default_environment_without_binding():
    payload = await worker._health_payload()
    assert payload["environment"] == "development"


class FalseyBindingValue:
    def __str__(self):
        return "production"
    def __bool__(self):
        return False


@pytest.mark.asyncio
async def test_health_payload_preserves_falsey_runtime_environment_binding():
    payload = await worker._health_payload(SimpleNamespace(ENVIRONMENT=FalseyBindingValue()))
    assert payload["environment"] == "production"


@pytest.mark.asyncio
async def test_storage_diagnostic_dispatch_guard_routes_authenticated_requests():
    monkeypatch = pytest.MonkeyPatch()
    try:
        monkeypatch.setattr(worker, "CloudflarePersistence", Persistence)
        env = SimpleNamespace(DB=DB(rows=[]), ENVIRONMENT="production", AUTH_TOKEN="secret")
        entry = worker.Default()
        entry.env = env
        headers = {"Authorization": "Bearer secret", "Content-Type": "application/json"}

        invalid = await entry.fetch(
            Request("POST", "https://x/api/v1/storage/diagnostic", None, headers)
        )
        assert "run_id is required" in str(invalid)

        valid = await entry.fetch(
            Request("POST", "https://x/api/v1/storage/diagnostic", {"run_id": "covered-run"}, headers)
        )
        assert "artifacts" in str(valid)
    finally:
        monkeypatch.undo()


@pytest.mark.asyncio
async def test_public_persistence_diagnostic_operations_are_forwarded(monkeypatch):
    forwarded_payload = {}

    async def fake_private_diagnostic(env, request, operation="infrastructure_verify", payload=None):
        if isinstance(payload, dict):
            forwarded_payload.update(payload)
        return {
            "ok": True,
            "operation": operation,
            "sentinel_id": "covered",
        }, 200

    monkeypatch.setattr(worker, "_operations_chatbot_diagnostic", fake_private_diagnostic)
    env = SimpleNamespace(DB=DB(rows=[]), ENVIRONMENT="production", AUTH_TOKEN="secret")
    entry = worker.Default()
    entry.env = env
    headers = {"Authorization": "Bearer secret", "Content-Type": "application/json"}

    seed = await entry.fetch(
        Request("POST", "https://x/api/v1/chatbot/diagnostic", {"operation": "persistence_seed"}, headers)
    )
    verify = await entry.fetch(
        Request("POST", "https://x/api/v1/chatbot/diagnostic", {"operation": "persistence_verify", "sentinel_id": "covered"}, headers)
    )

    assert "persistence_seed" in str(seed)
    assert "persistence_verify" in str(verify)
    assert forwarded_payload.get("sentinel_id") == "covered"
