from backend.admission import AdmissionOutcome, AdmissionPolicy, AdmissionRoute
from backend.admission_store import _handle_race_recheck


def test_race_recheck_blocks_released_non_protected_duplicate():
    decision, lease = _handle_race_recheck(
        {"released_at": 123},
        AdmissionRoute.CHEAP_READ,
        AdmissionPolicy(),
    )
    assert decision.outcome is AdmissionOutcome.RATE_LIMITED
    assert decision.allowed is False
    assert lease is None
