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


def policy(**overrides):
    values = dict(version=AdmissionPolicy.__dataclass_fields__["version"].default if False else "public-admission/v1", window_seconds=60, max_requests_per_subject=30, max_requests_global=300, max_concurrent_per_subject=22, max_concurrent_global=22, retry_after_seconds=5, protected_routes=(AdmissionRoute.CHAT, AdmissionRoute.RESEARCH, AdmissionRoute.STREAM))
    values.update(overrides)
    return AdmissionPolicy(**values)

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
