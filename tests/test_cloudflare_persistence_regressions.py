from types import SimpleNamespace

import pytest

from backend.persistence.cloudflare import CloudflarePersistence
from backend.api.models import ResearchRequest


class FakeStatement:
    def __init__(self, value=None):
        self.value = value

    def bind(self, *args):
        return self

    async def first(self):
        return self.value


class FakeDB:
    def __init__(self, run=None):
        self.run = run
        self.batch_result = [SimpleNamespace(results=[]), SimpleNamespace(results=[]), SimpleNamespace(results=[])]

    def prepare(self, sql):
        if sql.startswith("SELECT * FROM research_runs"):
            return FakeStatement(self.run)
        return FakeStatement()

    async def batch(self, statements):
        return self.batch_result


def request():
    return ResearchRequest(
        question="coverage regression",
        depth="standard",
        require_citations=True,
        max_sources=2,
        max_evidence_items=4,
        strict_zero_cost_only=True,
        source_urls=(),
    )


def persistence(db):
    return CloudflarePersistence(SimpleNamespace(DB=db, ARTIFACTS=None))


@pytest.mark.asyncio
async def test_create_run_idempotent_rejects_oversized_key():
    with pytest.raises(ValueError, match="exceeds maximum length"):
        await persistence(FakeDB()).create_run_idempotent(request(), "x" * 257)


@pytest.mark.asyncio
async def test_set_run_status_rejects_missing_run():
    with pytest.raises(ValueError, match="not found"):
        await persistence(FakeDB()).set_run_status("missing", "running")


@pytest.mark.asyncio
async def test_set_run_status_rejects_invalid_stored_status():
    db = FakeDB({"run_id": "run-1", "status": "corrupt"})
    with pytest.raises(ValueError, match="stored run status is invalid"):
        await persistence(db).set_run_status("run-1", "running")


@pytest.mark.asyncio
async def test_set_run_status_rejects_disallowed_transition():
    db = FakeDB({"run_id": "run-1", "status": "completed"})
    with pytest.raises(ValueError, match="invalid run transition"):
        await persistence(db).set_run_status("run-1", "running")
