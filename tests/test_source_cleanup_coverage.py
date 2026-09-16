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
    def __init__(self, headers=None):
        self.method = "GET"
        self.url = "https://example.invalid/api/v1/dashboard"
        self.headers = headers or {}

    async def json(self):
        return None


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
    authorized = await entry.fetch(Request({"Authorization": "Bearer secret"}))
    assert "dashboard" in str(authorized)
