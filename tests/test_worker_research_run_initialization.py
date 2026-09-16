from types import SimpleNamespace

import pytest

import worker


class _Headers:
    def get(self, _name):
        return None


class _Request:
    method = "POST"
    url = "https://example.test/api/v1/research"
    headers = _Headers()

    async def json(self):
        return {"question": "test"}


class _Persistence:
    def __init__(self, _env):
        pass

    async def create_run(self, _run_id, _req):
        raise RuntimeError("create failed")

    async def set_run_status(self, _run_id, _status):
        raise AssertionError("set_run_status must not run when run creation failed")


@pytest.mark.asyncio
async def test_research_run_creation_failure_preserves_original_error(monkeypatch):
    async def fake_json(_request):
        return {"question": "test"}

    monkeypatch.setattr(worker, "_authorized", lambda _request, _env: True)
    monkeypatch.setattr(worker, "_json", fake_json)
    monkeypatch.setattr(worker, "CloudflarePersistence", _Persistence)
    monkeypatch.setattr(worker, "submit_research", lambda _req: SimpleNamespace(ok=True, run_id="run-1", metadata={}))

    instance = worker.Default()
    instance.env = SimpleNamespace()
    response = await instance.fetch(_Request())
    body = await response.json()

    assert response.status == 503
    assert "create failed" in body["error"]
    assert "UnboundLocalError" not in body["error"]
