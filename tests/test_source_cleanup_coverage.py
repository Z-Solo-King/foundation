from types import SimpleNamespace

import pytest

import worker
from backend.worker_diagnostics import readiness_payload, storage_diagnostic


class _Statement:
    def __init__(self, value):
        self.value = value

    def bind(self, *args):
        return self

    async def first(self):
        return self.value

    async def all(self):
        return SimpleNamespace(results=self.value or [])


class _BrokenDB:
    def prepare(self, _sql):
        raise RuntimeError("database unavailable")


class _RowsDB:
    def __init__(self, rows):
        self.rows = rows

    def prepare(self, sql):
        if "artifact_ref" in sql:
            return _Statement(self.rows)
        return _Statement({"ok": 1})


class _Persistence:
    def __init__(self, *, artifacts=None, failure=None):
        self.artifacts = artifacts or {}
        self.failure = failure

    async def get_artifact(self, key):
        if self.failure == "get":
            raise RuntimeError("artifact read failed")
        return self.artifacts.get(key)


@pytest.mark.asyncio
async def test_readiness_payload_database_exception_fails_closed():
    body, status = await readiness_payload(SimpleNamespace(DB=_BrokenDB()))
    assert body["database"] is False
    assert status == 503


@pytest.mark.asyncio
async def test_storage_diagnostic_missing_artifact_fails_closed():
    body, status = await storage_diagnostic(
        SimpleNamespace(DB=_RowsDB([{"artifact_ref": "missing", "content_hash": "x", "content_length": 1}])) ,
        "run-1",
        persistence_cls=lambda env: _Persistence(artifacts={"missing": None}),
    )
    assert status == 503
    assert body["artifacts"][0]["error"] == "artifact not found"


@pytest.mark.asyncio
async def test_storage_diagnostic_hash_or_size_mismatch_fails_closed():
    body, status = await storage_diagnostic(
        SimpleNamespace(DB=_RowsDB([{"artifact_ref": "good", "content_hash": "bad", "content_length": 999}])),
        "run-2",
        persistence_cls=lambda env: _Persistence(artifacts={"good": b"abc"}),
    )
    assert status == 503
    assert body["artifacts"][0]["ok"] is False


class _Binding:
    def __init__(self, response=None, error=None):
        self.response = response
        self.error = error

    async def fetch(self, *_args):
        if self.error:
            raise self.error
        return self.response


class _Response:
    def __init__(self, status, payload):
        self.status = status
        self.payload = payload

    async def json(self):
        return self.payload


class _Request:
    def __init__(self, method="GET", url="https://example.invalid/api/v1/dashboard", headers=None):
        self.method = method
        self.url = url
        self.headers = headers or {}

    async def json(self):
        return None


@pytest.mark.asyncio
async def test_dashboard_binding_missing_invalid_and_exception_paths():
    body, status = await worker._operations_dashboard(SimpleNamespace(), _Request(headers={"Authorization": "Bearer token"}))
    assert status == 503
    assert body["error"] == "dashboard_backend_unavailable"

    body, status = await worker._operations_dashboard(
        SimpleNamespace(OPERATIONS=_Binding(_Response(200, []))),
        _Request(headers={"Authorization": "Bearer token"}),
    )
    assert status == 503
    assert body["error"] == "invalid_private_dashboard_response"

    body, status = await worker._operations_dashboard(
        SimpleNamespace(OPERATIONS=_Binding(error=RuntimeError("binding failed"))),
        _Request(),
    )
    assert status == 503
    assert body["error"] == "dashboard_backend_unavailable"


@pytest.mark.asyncio
async def test_dashboard_route_covers_auth_and_private_proxy():
    entry = worker.Default()
    entry.env = SimpleNamespace(
        AUTH_TOKEN="secret",
        OPERATIONS=_Binding(_Response(200, {"ok": True, "dashboard": {"healthy": True}})),
    )

    unauthorized = await entry.fetch(_Request(headers={}))
    assert "unauthorized" in str(unauthorized)

    authorized = await entry.fetch(_Request(headers={"Authorization": "Bearer secret"}))
    assert "dashboard" in str(authorized)
