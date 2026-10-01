from backend.admission import ADMISSION_CONTRACT_VERSION, AdmissionOutcome, AdmissionPolicy, AdmissionRoute

def policy():
    return AdmissionPolicy(
        version=ADMISSION_CONTRACT_VERSION,
        window_seconds=60,
        max_requests_per_subject=7,
        max_requests_global=70,
        max_concurrent_per_subject=4,
        max_concurrent_global=8,
        retry_after_seconds=3,
        protected_routes=(AdmissionRoute.CHAT, AdmissionRoute.RESEARCH, AdmissionRoute.STREAM),
    )
from backend.admission_store import _handle_race_recheck


def test_race_recheck_blocks_active_non_protected_duplicate():
    decision, lease = _handle_race_recheck(
        {"released_at": None},
        AdmissionRoute.CHEAP_READ,
        policy(),
    )
    assert decision.outcome is AdmissionOutcome.CONCURRENCY_LIMITED
    assert decision.allowed is False
    assert lease is None
