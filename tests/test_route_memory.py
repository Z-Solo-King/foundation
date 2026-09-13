import pytest

from backend.intelligence.planner_models import FailureClass
from backend.intelligence.route_memory import (
    RouteDisposition,
    RouteKey,
    RouteState,
    cooldown_seconds,
    disposition,
    eligible,
    record_failure,
    record_success,
    recover,
    update_memory,
)


def test_failure_backoff_quarantine_and_dispositions():
    state = RouteState()
    state = record_failure(state, FailureClass.TIMEOUT, 100.0)
    assert state.consecutive_failures == 1
    assert disposition(state, 100.1) is RouteDisposition.COOLDOWN
    state = record_failure(state, FailureClass.TIMEOUT, 120.0)
    state = record_failure(state, FailureClass.TIMEOUT, 160.0)
    assert disposition(state, 160.1) is RouteDisposition.QUARANTINED
    assert not eligible(state, 200.0)
    assert cooldown_seconds(state, FailureClass.POLICY) == 0.0


def test_policy_and_auth_failures_quarantine_immediately():
    state = record_failure(RouteState(), FailureClass.FORBIDDEN, 10.0)
    assert disposition(state, 10.1) is RouteDisposition.QUARANTINED
    assert not eligible(state, 11.0)


def test_success_clears_negative_memory_and_recovers():
    state = record_failure(RouteState(), FailureClass.TIMEOUT, 1.0)
    state = record_success(state, 1000.0)
    assert state.successes == 1
    assert state.consecutive_failures == 0
    assert state.cooldown_until is None
    assert state.quarantined_until is None
    assert disposition(state, 1000.1) is RouteDisposition.ELIGIBLE


def test_recover_respects_active_quarantine_then_clears_expired_quarantine():
    state = record_failure(RouteState(), FailureClass.CAPTCHA, 10.0)
    assert recover(state, 100.0) == state
    recovered = recover(state, state.quarantined_until + 1.0)
    assert recovered.quarantined_until is None
    assert recovered.consecutive_failures == 0


def test_route_identity_memory_isolated_and_validated():
    key = RouteKey("source-a", "api", "structured")
    state = RouteState(attempts=1)
    memory = update_memory({}, key, state)
    assert memory[key] == state
    with pytest.raises(ValueError):
        update_memory({}, RouteKey("", "api", "structured"), state)
    with pytest.raises(ValueError):
        record_failure(RouteState(), FailureClass.TIMEOUT, -1.0)
    with pytest.raises(ValueError):
        cooldown_seconds(RouteState(), FailureClass.TIMEOUT, base=0)
    with pytest.raises(ValueError):
        record_failure(RouteState(), FailureClass.TIMEOUT, 1.0, quarantine_after=0)
