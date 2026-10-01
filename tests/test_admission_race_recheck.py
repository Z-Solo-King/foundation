from backend.admission import ADMISSION_CONTRACT_VERSION, AdmissionOutcome, AdmissionPolicy, AdmissionRoute
def policy(**overrides):
    values = dict(
        version=ADMISSION_CONTRACT_VERSION,
        window_seconds=60,
        max_requests_per_subject=7,
        max_requests_global=70,
        max_concurrent_per_subject=4,
        max_concurrent_global=8,
        retry_after_seconds=3,
        protected_routes=(AdmissionRoute.CHAT, AdmissionRoute.RESEARCH, AdmissionRoute.STREAM),
    )
    values.update(overrides)
    return AdmissionPolicy(**values)


from backend.admission_store import _handle_race_recheck


def test_race_recheck_blocks_released_non_protected_duplicate():
    decision, lease = _handle_race_recheck(
        {"released_at": 123},
        AdmissionRoute.CHEAP_READ,
        policy(),
    )
    assert decision.outcome is AdmissionOutcome.RATE_LIMITED
    assert decision.allowed is False
    assert lease is None
