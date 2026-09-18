import pytest

from backend.admission import (
    ADMISSION_CONTRACT_VERSION,
    AdmissionOutcome,
    AdmissionPolicy,
    AdmissionRoute,
    AdmissionSnapshot,
    decide_admission,
)


def snapshot(**changes):
    values = dict(
        authority_available=True,
        subject_requests=0,
        global_requests=0,
        subject_concurrent=0,
        global_concurrent=0,
    )
    values.update(changes)
    return AdmissionSnapshot(**values)


def test_admission_accepts_within_burst_and_concurrency_limits():
    decision = decide_admission(
        policy=AdmissionPolicy(),
        snapshot=snapshot(),
        subject_fingerprint="subject-1",
        route=AdmissionRoute.RESEARCH,
    )
    assert decision.allowed is True
    assert decision.outcome is AdmissionOutcome.ACCEPTED
    assert decision.contract_version == ADMISSION_CONTRACT_VERSION
    assert decision.retry_after_header is None


def test_global_and_subject_request_limits_fail_closed():
    policy = AdmissionPolicy()
    assert decide_admission(policy=policy, snapshot=snapshot(global_requests=300), subject_fingerprint="s", route=AdmissionRoute.RESEARCH).outcome is AdmissionOutcome.RATE_LIMITED
    assert decide_admission(policy=policy, snapshot=snapshot(subject_requests=30), subject_fingerprint="s", route=AdmissionRoute.RESEARCH).outcome is AdmissionOutcome.RATE_LIMITED


def test_global_and_subject_concurrency_limits_fail_closed():
    policy = AdmissionPolicy()
    assert decide_admission(policy=policy, snapshot=snapshot(global_concurrent=20), subject_fingerprint="s", route=AdmissionRoute.CHAT).outcome is AdmissionOutcome.CONCURRENCY_LIMITED
    assert decide_admission(policy=policy, snapshot=snapshot(subject_concurrent=2), subject_fingerprint="s", route=AdmissionRoute.CHAT).outcome is AdmissionOutcome.CONCURRENCY_LIMITED


def test_duplicate_suppression_does_not_create_second_resource_authority():
    decision = decide_admission(
        policy=AdmissionPolicy(),
        snapshot=snapshot(),
        subject_fingerprint="s",
        route=AdmissionRoute.CHAT,
        duplicate=True,
    )
    assert decision.outcome is AdmissionOutcome.DUPLICATE
    assert decision.allowed is False


def test_unavailable_authority_fails_closed_for_protected_routes_and_allows_cheap_reads():
    protected = decide_admission(
        policy=AdmissionPolicy(),
        snapshot=snapshot(authority_available=False),
        subject_fingerprint="s",
        route=AdmissionRoute.RESEARCH,
    )
    assert protected.outcome is AdmissionOutcome.AUTHORITY_UNAVAILABLE
    assert protected.retry_after_header == "5"

    cheap = decide_admission(
        policy=AdmissionPolicy(),
        snapshot=snapshot(authority_available=False),
        subject_fingerprint="s",
        route=AdmissionRoute.CHEAP_READ,
    )
    assert cheap.outcome is AdmissionOutcome.ACCEPTED


def test_policy_and_snapshot_validation_fail_closed():
    with pytest.raises(ValueError):
        AdmissionPolicy(version="v0").validate()
    with pytest.raises(ValueError):
        AdmissionPolicy(window_seconds=0).validate()
    with pytest.raises(ValueError):
        AdmissionSnapshot(authority_available=True, global_requests=-1).validate()
    with pytest.raises(ValueError):
        decide_admission(policy=AdmissionPolicy(), snapshot=snapshot(), subject_fingerprint=" ", route=AdmissionRoute.CHAT)
