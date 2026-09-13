from types import SimpleNamespace

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
        return Statement(self.rows if "artifact_ref" in sql else self.run)


class Statement:
    def __init__(self, value):
        self.value = value

    def bind(self, *args):
        return self

    async def first(self):
        return self.value

    async def all(self):
        return SimpleNamespace(results=self.value or [])


class BrokenDB:
    def prepare(self, sql):
        raise RuntimeError("d1 unavailable")


class Control:
    async def fetch(self, url, init=None):
        return SimpleNamespace(status=200, json=lambda: _json_value({"ok": True, "path": url}))


class BrokenControl:
    async def fetch(self, url, init=None):
        raise RuntimeError("control down")


async def _json_value(value):
    return value


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


class BrokenPersistence(Persistence):
    async def create_run(self, run_id, request):
        raise RuntimeError("persistence down")

    async def create_run_idempotent(self, request, idempotency_key):
        raise RuntimeError("idempotency down")


@pytest.mark.asyncio
async def test_control_plane_chatbot_diagnostic_routes_success_and_failures(monkeypatch):
    monkeypatch.setattr(worker, "CloudflarePersistence", Persistence)
    body, status = await worker._control_plane_chatbot_diagnostic(SimpleNamespace(CONTROL_PLANE=Control()), {"operation": "knowledge", "question": "Explain testing"})
    assert status == 200 and body["ok"] is True
    body, status = await worker._control_plane_chatbot_diagnostic(SimpleNamespace(CONTROL_PLANE=None), {"operation": "knowledge", "question": "Explain testing"})
    assert status == 503 and "service binding" in body["error"]
    body, status = await worker._control_plane_chatbot_diagnostic(SimpleNamespace(CONTROL_PLANE=BrokenControl()), {"operation": "knowledge", "question": "Explain testing"})
    assert status == 503 and "diagnostic failure" in body["error"]


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
async def test_worker_http_diagnostic_and_research_fail_closed_paths(monkeypatch):
    monkeypatch.setattr(worker, "CloudflarePersistence", Persistence)
    env = SimpleNamespace(DB=DB(rows=[]), ENVIRONMENT="production", AUTH_TOKEN="secret", CONTROL_PLANE=Control())
    entry = worker.Default()
    entry.env = env

    unauthorized = await entry.fetch(Request("POST", "https://x/api/v1/chatbot/diagnostic", {"operation": "knowledge"}, {"Authorization": "Bearer bad"}))
    assert "unauthorized" in str(unauthorized)
    invalid = await entry.fetch(Request("POST", "https://x/api/v1/chatbot/diagnostic", [], {"Authorization": "Bearer secret"}))
    assert "invalid JSON object" in str(invalid)
    chatbot = await entry.fetch(Request("POST", "https://x/api/v1/chatbot/diagnostic", {"operation": "knowledge", "question": "Explain testing"}, {"Authorization": "Bearer secret"}))
    assert "ok" in str(chatbot)

    storage_unauthorized = await entry.fetch(Request("POST", "https://x/api/v1/storage/diagnostic", {"run_id": "run-1"}, {"Authorization": "Bearer bad"}))
    assert "unauthorized" in str(storage_unauthorized)
    no_run = await entry.fetch(Request("POST", "https://x/api/v1/storage/diagnostic", {}, {"Authorization": "Bearer secret"}))
    assert "run_id" in str(no_run)
    storage = await entry.fetch(Request("POST", "https://x/api/v1/storage/diagnostic", {"run_id": "run-1"}, {"Authorization": "Bearer secret"}))
    assert "artifacts" in str(storage)
    async def broken_storage(*args, **kwargs):
        raise RuntimeError("storage diagnostic exploded")
    monkeypatch.setattr(worker, "_storage_diagnostic", broken_storage)
    failed_storage = await entry.fetch(Request("POST", "https://x/api/v1/storage/diagnostic", {"run_id": "run-1"}, {"Authorization": "Bearer secret"}))
    assert "storage diagnostic failure" in str(failed_storage)

    missing = await entry.fetch(Request("GET", "https://x/api/v1/research/missing", None, {"Authorization": "Bearer secret"}))
    assert "run not found" in str(missing)
    persistence_error = worker.Default()
    persistence_error.env = SimpleNamespace(DB=BrokenDB(), ENVIRONMENT="production", AUTH_TOKEN="secret", CONTROL_PLANE=Control())
    failed_get = await persistence_error.fetch(Request("GET", "https://x/api/v1/research/run-1", None, {"Authorization": "Bearer secret"}))
    assert "persistence failure" in str(failed_get)

    invalid_research = await entry.fetch(Request("POST", "https://x/api/v1/research", [], {"Authorization": "Bearer secret"}))
    assert "invalid JSON object" in str(invalid_research)
    bad_shape = await entry.fetch(Request("POST", "https://x/api/v1/research", {"question": "x", "unexpected": True}, {"Authorization": "Bearer secret"}))
    assert "unexpected" in str(bad_shape)
    rejected = await entry.fetch(Request("POST", "https://x/api/v1/research", {"question": "x", "strict_zero_cost_only": False}, {"Authorization": "Bearer secret"}))
    assert "strict $0 cost mode" in str(rejected)


@pytest.mark.asyncio
async def test_research_persistence_failures_and_idempotency(monkeypatch):
    monkeypatch.setattr(worker, "CloudflarePersistence", BrokenPersistence)
    entry = worker.Default()
    entry.env = SimpleNamespace(DB=DB(), ENVIRONMENT="production", AUTH_TOKEN="secret", CONTROL_PLANE=Control())
    request = Request("POST", "https://x/api/v1/research", {"question": "x", "source_urls": [], "strict_zero_cost_only": True}, {"Authorization": "Bearer secret"})
    failed = await entry.fetch(request)
    assert "execution/persistence failure" in str(failed)
    request.headers["Idempotency-Key"] = "key-1"
    failed_idempotent = await entry.fetch(request)
    assert "execution/persistence failure" in str(failed_idempotent)
