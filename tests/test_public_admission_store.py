import pytest

from backend.admission import AdmissionPolicy, AdmissionRoute
from backend.admission_store import D1AdmissionStore, ROUTE_COST_UNITS


class FakeStatement:
    def __init__(self, query):
        self.query = query
        self.args = ()

    def bind(self, *args):
        self.args = args
        return self

    async def run(self):
        return {"meta": {"changes": 1}}

    async def first(self):
        return {
            "subject_requests": 0,
            "global_requests": 0,
            "subject_concurrent": 0,
            "global_concurrent": 0,
        }


class FakeDB:
    def __init__(self):
        self.queries = []

    def prepare(self, query):
        self.queries.append(query)
        return FakeStatement(query)


@pytest.mark.asyncio
async def test_d1_store_admits_with_existing_admission_policy():
    db = FakeDB()
    store = D1AdmissionStore(db)
    decision, lease = await store.acquire(
        subject_fingerprint="subject-1",
        route=AdmissionRoute.RESEARCH,
        policy=AdmissionPolicy(),
        event_id="event-1",
        now=120,
    )
    assert decision.allowed is True
    assert lease is not None
    assert lease.event_id == "event-1"
    assert lease.cost_units == 5
    assert any("public_admission_events" in query for query in db.queries)


@pytest.mark.asyncio
async def test_d1_store_release_is_idempotent_at_statement_level():
    db = FakeDB()
    store = D1AdmissionStore(db)
    decision, lease = await store.acquire(
        subject_fingerprint="subject-1",
        route=AdmissionRoute.CHAT,
        policy=AdmissionPolicy(),
        event_id="event-1",
        now=120,
    )
    assert decision.allowed and lease is not None
    await store.release(lease)
    await store.release(lease)
    assert sum("UPDATE public_admission_events" in query for query in db.queries) == 2


def test_route_cost_classes_are_explicit_and_bounded():
    policy = AdmissionPolicy()
    assert set(ROUTE_COST_UNITS) == {
        AdmissionRoute.CHEAP_READ,
        AdmissionRoute.CHAT,
        AdmissionRoute.RESEARCH,
        AdmissionRoute.STREAM,
    }
    assert ROUTE_COST_UNITS[AdmissionRoute.RESEARCH] > ROUTE_COST_UNITS[AdmissionRoute.CHAT]
    policy.validate()


def test_public_worker_rejects_expensive_paths_before_upstream_call_source_contract():
    source = open("worker.py", encoding="utf-8").read()
    assert "AdmissionRoute.CHAT" in source
    assert "AdmissionRoute.RESEARCH" in source
    assert "_operations_chat(self.env" in source
    assert "_operations_chat_stream(self.env" in source
    assert "await _public_admit" in source
