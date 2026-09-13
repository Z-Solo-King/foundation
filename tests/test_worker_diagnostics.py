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
async def test_worker_http_diagnostic_routes_are_authenticated(monkeypatch):
    env = SimpleNamespace(DB=DB(rows=[]), ENVIRONMENT="production", AUTH_TOKEN="secret", CONTROL_PLANE=Control())
    entry = worker.Default()
    entry.env = env

    unauthorized = await entry.fetch(Request("POST", "https://x/api/v1/chatbot/diagnostic", {"operation": "knowledge"}, {"Authorization": "Bearer bad"}))
    assert "unauthorized" in str(unauthorized)
    chatbot = await entry.fetch(Request("POST", "https://x/api/v1/chatbot/diagnostic", {"operation": "knowledge", "question": "Explain testing"}, {"Authorization": "Bearer secret"}))
    assert "ok" in str(chatbot)

    no_run = await entry.fetch(Request("POST", "https://x/api/v1/storage/diagnostic", {}, {"Authorization": "Bearer secret"}))
    assert "run_id" in str(no_run)
    storage = await entry.fetch(Request("POST", "https://x/api/v1/storage/diagnostic", {"run_id": "run-1"}, {"Authorization": "Bearer secret"}))
    assert "artifacts" in str(storage)
