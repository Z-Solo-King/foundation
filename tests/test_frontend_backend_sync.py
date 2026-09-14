from types import SimpleNamespace

import pytest

import worker
from backend.api.models import ResearchRequest


class FakeStatement:
    def __init__(self, value=None):
        self.value = value
        self.bound = ()

    def bind(self, *args):
        self.bound = args
        return self

    async def run(self):
        return {"success": True}

    async def first(self):
        return self.value

    async def all(self):
        return self.value or []


class FakeDB:
    def __init__(self):
        self.status = "planned"

    def prepare(self, sql):
        if sql.startswith("SELECT * FROM research_runs"):
            return FakeStatement({"run_id": "r1", "status": self.status})
        return FakeStatement(SimpleNamespace(results=[]))


class FakePersistence:
    def __init__(self):
        self.status = "planned"
        self.created = []

    async def create_run(self, run_id, request):
        self.created.append((run_id, request))
        return run_id

    async def create_run_idempotent(self, request, key):
        self.created.append(("idempotent", request, key))
        return "idempotent-run"

    async def set_run_status(self, run_id, status):
        self.status = status


@pytest.mark.asyncio
async def test_worker_extracts_bounded_urls_and_reports_capability_boundary(monkeypatch):
    assert worker._extract_source_urls("Inspect https://example.com/a, and https://example.org/b") == (
        "https://example.com/a",
        "https://example.org/b",
    )
    assert worker._extract_source_urls("x https://example.com https://example.com") == ("https://example.com",)

    persistence = FakePersistence()
    monkeypatch.setattr(worker, "CloudflarePersistence", lambda env: persistence)
    monkeypatch.setattr(worker, "submit_research", lambda request: SimpleNamespace(ok=True, run_id="r1", metadata={"strict_zero_cost_only": True}))

    async def ingest(env, run_id, request):
        return [{"url": request.source_urls[0], "access_state": "accessible", "retrieval_method": "http_fetch"}]

    monkeypatch.setattr(worker, "_ingest_sources", ingest)

    class Request:
        method = "POST"
        url = "https://worker/api/v1/research"
        headers = {"Authorization": "Bearer secret"}

        async def json(self):
            return {"question": "Inspect https://example.com", "strict_zero_cost_only": True}

    entry = worker.Default()
    entry.env = SimpleNamespace(ENVIRONMENT="production", AUTH_TOKEN="secret", DB=FakeDB(), ARTIFACTS=SimpleNamespace())
    response = await entry.fetch(Request())
    assert "source_url_ingestion" in str(response)
    assert persistence.status == "completed"


@pytest.mark.asyncio
async def test_worker_stays_honest_when_no_source_urls_are_available(monkeypatch):
    persistence = FakePersistence()
    monkeypatch.setattr(worker, "CloudflarePersistence", lambda env: persistence)
    monkeypatch.setattr(worker, "submit_research", lambda request: SimpleNamespace(ok=True, run_id="r1", metadata={"strict_zero_cost_only": True}))

    class Request:
        method = "POST"
        url = "https://worker/api/v1/research"
        headers = {"Authorization": "Bearer secret"}

        async def json(self):
            return {"question": "General question", "strict_zero_cost_only": True}

    entry = worker.Default()
    entry.env = SimpleNamespace(ENVIRONMENT="production", AUTH_TOKEN="secret", DB=FakeDB(), ARTIFACTS=SimpleNamespace())
    response = await entry.fetch(Request())
    assert "awaiting_source_urls" in str(response)
    assert persistence.status == "planned"


@pytest.mark.asyncio
async def test_get_run_exposes_ui_consumable_backend_contract():
    db = FakeDB()
    payload = await worker._get_run(SimpleNamespace(DB=db), "r1")
    assert payload["status"] == "planned"
    assert payload["result"] is None
    assert payload["synthesis_available"] is False
    assert payload["capabilities"]["source_url_ingestion"] is True
    assert payload["capabilities"]["general_web_discovery"] is False
    assert payload["capabilities"]["evidence_synthesis"] is False
