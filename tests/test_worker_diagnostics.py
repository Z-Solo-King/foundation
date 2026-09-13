import json
from types import SimpleNamespace

import pytest

import worker
from worker import Request


class DB:
    def __init__(self, rows):
        self.rows = rows


class Persistence:
    def __init__(self, env):
        self.env = env

    async def list_artifacts_for_run(self, run_id):
        return list(self.env.DB.rows)


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
    entry = worker.Default()
    entry.env = env

    unauthorized = await entry.fetch(Request("POST", "https://x/api/v1/chatbot/diagnostic", [], {}))
    assert "unauthorized" in str(unauthorized)

    auth_headers = {"Authorization": "Bearer secret"}
    public_invalid = await entry.fetch(Request("POST", "https://x/api/v1/chatbot/diagnostic", [], auth_headers))
    assert "invalid JSON object" in str(public_invalid)
    unsupported = await entry.fetch(Request("POST", "https://x/api/v1/chatbot/diagnostic", {"operation": "knowledge"}, auth_headers))
    assert "unsupported public diagnostic operation" in str(unsupported)

    public_test = await entry.fetch(Request("POST", "https://x/api/v1/chatbot/diagnostic", {"operation": "infrastructure_verify_public_test"}, auth_headers))
    assert "checks" in str(public_test)

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
