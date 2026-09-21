from types import SimpleNamespace

import pytest

import worker
from backend.worker_diagnostics import readiness_payload, storage_diagnostic


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
    def prepare(self, _sql):
        raise RuntimeError("database unavailable")


class RowsDB:
    def __init__(self, rows):
        self.rows = rows

    def prepare(self, sql):
        return Statement(self.rows) if "artifact_ref" in sql else Statement({"ok": 1})


class Persistence:
    def __init__(self, artifacts):
        self.artifacts = artifacts

    async def get_artifact(self, key):
        return self.artifacts.get(key)


class Response:
    def __init__(self, status, payload):
        self.status = status
        self.payload = payload

    async def json(self):
        return self.payload


class Binding:
    def __init__(self, response=None, error=None):
        self.response = response
        self.error = error

    async def fetch(self, *_args):
        if self.error:
            raise self.error
        return self.response


class Request:
    def __init__(self, method="GET", url="https://example.invalid/api/v1/dashboard", headers=None):
        self.method = method
        self.url = url
        self.headers = headers or {}

    async def json(self):
        return None


def test_service_request_carries_abort_signal(monkeypatch):
    import sys
    from types import ModuleType

    signal = object()

    class FakeRequest:
        @staticmethod
        def new(url, init):
            return {"url": url, **init}

    fake_js = ModuleType("js")
    fake_js.Object = SimpleNamespace(fromEntries=lambda value: value)
    fake_js.Request = FakeRequest

    fake_ffi = ModuleType("pyodide.ffi")
    fake_ffi.to_js = lambda value, **kwargs: value
    fake_pyodide = ModuleType("pyodide")
    fake_pyodide.ffi = fake_ffi

    monkeypatch.setitem(sys.modules, "js", fake_js)
    monkeypatch.setitem(sys.modules, "pyodide", fake_pyodide)
    monkeypatch.setitem(sys.modules, "pyodide.ffi", fake_ffi)

    request = worker._service_request(
        "https://chat/v1/chat",
        method="POST",
        headers={"Authorization": "Bearer token"},
        body="{}",
        signal=signal,
    )
    assert request["signal"] is signal


@pytest.mark.asyncio
async def test_readiness_database_exception_fails_closed():
    body, status = await readiness_payload(SimpleNamespace(DB=BrokenDB()))
    assert body["database"] is False
    assert status == 503


@pytest.mark.asyncio
async def test_storage_missing_and_mismatch_fail_closed():
    rows = [{"artifact_ref": "missing", "content_hash": "x", "content_length": 1}]
    body, status = await storage_diagnostic(SimpleNamespace(DB=RowsDB(rows)), "run-1", persistence_cls=lambda env: Persistence({"missing": None}))
    assert status == 503 and body["artifacts"][0]["error"] == "artifact not found"

    rows = [{"artifact_ref": "good", "content_hash": "bad", "content_length": 999}]
    body, status = await storage_diagnostic(SimpleNamespace(DB=RowsDB(rows)), "run-2", persistence_cls=lambda env: Persistence({"good": b"abc"}))
    assert status == 503 and body["artifacts"][0]["ok"] is False


@pytest.mark.asyncio
async def test_dashboard_route_auth_and_proxy_paths():
    entry = worker.Default()
    entry.env = SimpleNamespace(AUTH_TOKEN="secret", OPERATIONS=Binding(Response(200, {"ok": True, "dashboard": {"healthy": True}})))
    unauthorized = await entry.fetch(Request())
    assert "unauthorized" in str(unauthorized)
    authorized = await entry.fetch(Request(headers={"Authorization": "Bearer secret"}))
    assert "dashboard" in str(authorized)


@pytest.mark.asyncio
async def test_private_chatbot_diagnostic_paths():
    body, status = await worker._operations_chatbot_diagnostic(SimpleNamespace())
    assert status == 503 and body["error"] == "chat_backend_unavailable"

    healthy = {"ok": True, "chatbot": {"allowed": True}, "runtime_status": "ok", "runtime_checks": [{"name": "d1_memory_store", "ok": True}], "provider_policy": {"strict_zero_cost_only": True}}
    body, status = await worker._operations_chatbot_diagnostic(SimpleNamespace(OPERATIONS=Binding(Response(200, healthy))))
    assert status == 200 and body["ok"] is True
    assert body["chatbot"]["allowed"] is True

    malformed = await worker._operations_chatbot_diagnostic(SimpleNamespace(OPERATIONS=Binding(Response(200, []))))
    assert malformed[1] == 503
    assert malformed[0]["error"] == "invalid_private_chatbot_diagnostic"

    rejected = await worker._operations_chatbot_diagnostic(SimpleNamespace(OPERATIONS=Binding(Response(503, {"ok": False, "error": "unavailable"}))))
    assert rejected[1] == 503
    assert rejected[0]["response_status"] == 503
    failed = await worker._operations_chatbot_diagnostic(SimpleNamespace(OPERATIONS=Binding(error=RuntimeError("binding failed"))))
    assert failed[1] == 503
    assert "binding failure" in failed[0]["error"]
