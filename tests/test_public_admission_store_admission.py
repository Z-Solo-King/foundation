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

def test_public_admission_insert_is_idempotent_source_contract():
    source = open("backend/admission_store.py", encoding="utf-8").read()
    assert "INSERT OR IGNORE INTO public_admission_events" in source


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


def test_admission_response_emits_retry_after_header():
    import worker
    from backend.admission import AdmissionDecision, AdmissionOutcome

    response = worker._admission_response(
        AdmissionDecision(
            AdmissionOutcome.RATE_LIMITED,
            AdmissionRoute.RESEARCH,
            False,
            "rate limited",
            retry_after_seconds=7,
        )
    )
    assert response.status == 429
    assert response.headers["Retry-After"] == "7"



def test_admission_response_without_retry_after_header():
    import worker
    from backend.admission import AdmissionDecision, AdmissionOutcome

    response = worker._admission_response(
        AdmissionDecision(
            AdmissionOutcome.RATE_LIMITED,
            AdmissionRoute.RESEARCH,
            False,
            "rate limited",
            retry_after_seconds=0,
        )
    )
    assert response.status == 429
    assert "Retry-After" not in response.headers


