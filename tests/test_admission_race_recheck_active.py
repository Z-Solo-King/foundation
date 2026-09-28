from backend.admission import AdmissionOutcome, AdmissionPolicy, AdmissionRoute
from backend.admission_store import _handle_race_recheck


def test_race_recheck_blocks_active_non_protected_duplicate():
    decision, lease = _handle_race_recheck(
        {"released_at": None},
        AdmissionRoute.CHEAP_READ,
        AdmissionPolicy(),
    )
    assert decision.outcome is AdmissionOutcome.CONCURRENCY_LIMITED
    assert decision.allowed is False
    assert lease is None
