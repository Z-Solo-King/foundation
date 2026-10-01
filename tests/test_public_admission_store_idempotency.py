from __future__ import annotations

import asyncio
import pytest

from backend.admission import AdmissionDecision, AdmissionOutcome, AdmissionPolicy, AdmissionRoute
from backend.admission_store import D1AdmissionStore, ROUTE_COST_UNITS, _insert_new_admission, _storage_event_id
from tests.admission_store_support import (
    FakeDB,
    Request,
    AdmissionLeaseTracker,
    Persistence,
    accepted_admission,
    ZeroInsertDB,
    IdempotentAdmissionDB,
)

def test_d1_store_replays_same_event_without_a_second_admission_slot():
    import asyncio

    db = IdempotentAdmissionDB()
    store = D1AdmissionStore(db)
    policy = AdmissionPolicy()

    first_decision, first_lease = asyncio.run(
        store.acquire(
            subject_fingerprint="subject-1",
            route=AdmissionRoute.CHAT,
            policy=policy,
            event_id="replay-key",
            now=120,
        )
    )
    assert first_decision.allowed is True
    assert first_lease is not None
    asyncio.run(store.release(first_lease))

    second_decision, second_lease = asyncio.run(
        store.acquire(
            subject_fingerprint="subject-1",
            route=AdmissionRoute.CHAT,
            policy=policy,
            event_id="replay-key",
            now=121,
        )
    )
    assert second_decision.allowed is True
    assert second_lease is None


def test_d1_store_rejects_replay_across_admission_scopes():
    import asyncio

    db = IdempotentAdmissionDB()
    db.events["scope-key"] = {
        "event_id": "scope-key",
        "window_start": 120,
        "subject_fingerprint": "other-subject",
        "route": "chat",
        "cost_units": 2,
        "lease_expires_at": 180,
        "released_at": 150,
    }
    decision, lease = asyncio.run(
        D1AdmissionStore(db).acquire(
            subject_fingerprint="subject-1",
            route=AdmissionRoute.CHAT,
            policy=AdmissionPolicy(),
            event_id="scope-key",
            now=121,
        )
    )
    assert decision.outcome.value == "duplicate"
    assert decision.allowed is False
    assert lease is None


def test_d1_store_reclaims_expired_admission_lease():
    import asyncio

    db = IdempotentAdmissionDB()
    store = D1AdmissionStore(db)
    first_decision, first_lease = asyncio.run(
        store.acquire(
            subject_fingerprint="subject-1",
            route=AdmissionRoute.CHAT,
            policy=AdmissionPolicy(),
            event_id="expired-key",
            now=120,
        )
    )
    assert first_decision.allowed is True
    assert first_lease is not None
    db.events[_storage_event_id("subject-1", "expired-key")]["lease_expires_at"] = 0

    decision, lease = asyncio.run(
        store.acquire(
            subject_fingerprint="subject-1",
            route=AdmissionRoute.CHAT,
            policy=AdmissionPolicy(),
            event_id="expired-key",
            now=121,
        )
    )
    assert decision.allowed is True
    assert lease is not None
    assert lease.expires_at == 181


def test_d1_store_keeps_released_non_idempotent_duplicate_on_admission_decision():
    import asyncio

    db = IdempotentAdmissionDB()
    db.events["cheap-key"] = {
        "event_id": "cheap-key",
        "window_start": 120,
        "subject_fingerprint": "subject-1",
        "route": "cheap_read",
        "cost_units": 1,
        "lease_expires_at": 180,
        "released_at": 150,
    }
    decision, lease = asyncio.run(
        D1AdmissionStore(db).acquire(
            subject_fingerprint="subject-1",
            route=AdmissionRoute.CHEAP_READ,
            policy=AdmissionPolicy(),
            event_id="cheap-key",
            now=121,
        )
    )
    assert decision.outcome is AdmissionOutcome.RATE_LIMITED
    assert decision.allowed is False
    assert lease is None


def test_d1_store_blocks_active_non_idempotent_duplicate():
    import asyncio

    db = IdempotentAdmissionDB()
    store = D1AdmissionStore(db)
    first_decision, first_lease = asyncio.run(
        store.acquire(
            subject_fingerprint="subject-1",
            route=AdmissionRoute.CHEAP_READ,
            policy=AdmissionPolicy(),
            event_id="cheap-active-key",
            now=120,
        )
    )
    assert first_decision.allowed is True
    assert first_lease is not None

    decision, lease = asyncio.run(
        store.acquire(
            subject_fingerprint="subject-1",
            route=AdmissionRoute.CHEAP_READ,
            policy=AdmissionPolicy(),
            event_id="cheap-active-key",
            now=121,
        )
    )
    assert decision.outcome.value == "concurrency_limited"
    assert decision.allowed is False
    assert lease is None


def test_d1_store_delegates_active_chat_duplicate_to_idempotency_authority():
    import asyncio

    db = IdempotentAdmissionDB()
    store = D1AdmissionStore(db)
    first_decision, first_lease = asyncio.run(
        store.acquire(
            subject_fingerprint="subject-1",
            route=AdmissionRoute.CHAT,
            policy=AdmissionPolicy(),
            event_id="active-key",
            now=120,
        )
    )
    assert first_decision.allowed is True
    assert first_lease is not None

    decision, lease = asyncio.run(
        store.acquire(
            subject_fingerprint="subject-1",
            route=AdmissionRoute.CHAT,
            policy=AdmissionPolicy(),
            event_id="active-key",
            now=121,
        )
    )
    assert decision.outcome.value == "accepted"
    assert decision.allowed is True
    assert lease is None


def test_d1_store_delegates_active_stream_duplicate_to_idempotency_authority():
    import asyncio

    db = IdempotentAdmissionDB()
    store = D1AdmissionStore(db)
    first_decision, first_lease = asyncio.run(
        store.acquire(
            subject_fingerprint="subject-1",
            route=AdmissionRoute.STREAM,
            policy=AdmissionPolicy(),
            event_id="active-stream-key",
            now=120,
        )
    )
    assert first_decision.allowed is True
    assert first_lease is not None

    decision, lease = asyncio.run(
        store.acquire(
            subject_fingerprint="subject-1",
            route=AdmissionRoute.STREAM,
            policy=AdmissionPolicy(),
            event_id="active-stream-key",
            now=121,
        )
    )
    assert decision.outcome.value == "accepted"
    assert decision.allowed is True
    assert lease is None


def test_d1_store_delegates_active_research_duplicate_to_idempotency_authority():
    import asyncio

    db = IdempotentAdmissionDB()
    store = D1AdmissionStore(db)
    first_decision, first_lease = asyncio.run(
        store.acquire(
            subject_fingerprint="subject-1",
            route=AdmissionRoute.RESEARCH,
            policy=AdmissionPolicy(),
            event_id="active-research-key",
            now=120,
        )
    )
    assert first_decision.allowed is True
    assert first_lease is not None

    decision, lease = asyncio.run(
        store.acquire(
            subject_fingerprint="subject-1",
            route=AdmissionRoute.RESEARCH,
            policy=AdmissionPolicy(),
            event_id="active-research-key",
            now=121,
        )
    )
    assert decision.outcome.value == "accepted"
    assert decision.allowed is True
    assert lease is None


def test_d1_store_delegates_chat_after_failed_lease_reclaim_race():
    import asyncio

    db = IdempotentAdmissionDB()
    store = D1AdmissionStore(db)
    first_decision, first_lease = asyncio.run(
        store.acquire(
            subject_fingerprint="subject-1",
            route=AdmissionRoute.CHAT,
            policy=AdmissionPolicy(),
            event_id="reclaim-race-key",
            now=120,
        )
    )
    assert first_decision.allowed is True
    assert first_lease is not None
    db.events[_storage_event_id("subject-1", "reclaim-race-key")]["lease_expires_at"] = 0
    db.reclaim_changes = 0

    decision, lease = asyncio.run(
        store.acquire(
            subject_fingerprint="subject-1",
            route=AdmissionRoute.CHAT,
            policy=AdmissionPolicy(),
            event_id="reclaim-race-key",
            now=121,
        )
    )
    assert decision.outcome.value == "accepted"
    assert decision.allowed is True
    assert lease is None


def test_admission_decision_uses_weighted_cost_fields():
    from backend.admission import AdmissionSnapshot, decide_admission

    policy = AdmissionPolicy()
    accepted = decide_admission(
        policy=policy,
        snapshot=AdmissionSnapshot(authority_available=True, subject_cost_units=29),
        subject_fingerprint="subject-1",
        route=AdmissionRoute.CHAT,
    )
    denied = decide_admission(
        policy=policy,
        snapshot=AdmissionSnapshot(authority_available=True, subject_cost_units=30),
        subject_fingerprint="subject-1",
        route=AdmissionRoute.CHAT,
    )
    assert accepted.allowed is True
    assert denied.allowed is False
    assert denied.outcome.value == "rate_limited"


def test_admission_storage_identity_is_subject_scoped():
    assert _storage_event_id("subject-a", "same") != _storage_event_id("subject-b", "same")


def test_admission_store_samples_cleanup_instead_of_deleting_every_request():
    source = open("backend/admission_store.py", encoding="utf-8").read()
    assert "if now % (policy.window_seconds * 10) == 0:" in source


def test_admission_store_uses_weighted_atomic_insert_guard():
    source = open("backend/admission_store.py", encoding="utf-8").read()
    assert "COALESCE(SUM(cost_units), 0)" in source
    assert " + ? <= ?" in source


def test_duplicate_admission_is_http_conflict():
    import worker
    from backend.admission import AdmissionDecision, AdmissionOutcome

    response = worker._admission_response(
        AdmissionDecision(
            AdmissionOutcome.DUPLICATE,
            AdmissionRoute.CHAT,
            False,
            "duplicate",
        )
    )
    assert response.status == 409


def test_duplicate_spend_rejects_when_subject_cost_ceiling_would_be_exceeded():
    class DB:
        def __init__(self):
            self.calls = 0

        def prepare(self, query):
            parent = self
            class Statement:
                def bind(self_inner, *args):
                    self_inner.args = args
                    return self_inner
                async def first(self_inner):
                    return {"total_cost": 30}
                async def run(self_inner):
                    parent.calls += 1
                    return {"meta": {"changes": 0}}
            return Statement()
    from backend.admission_store import _charge_duplicate_spend
    assert asyncio.run(_charge_duplicate_spend(
        DB(),
        event_id="x",
        subject_fingerprint="s",
        window_start=0,
        cost_units=1,
        max_cost_units=30,
    )) is False



def test_admission_identity_rejects_oversized_event_id():
    with pytest.raises(ValueError, match="exceeds supported size"):
        D1AdmissionStore._validate_identity("subject-1", "x" * 257)


