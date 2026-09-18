import pytest

from backend.sources.fallbacks import (
    AcquisitionFallbackPolicy,
    AcquisitionLane,
    AcquisitionLaneKind,
    AcquisitionOutcome,
    choose_next_lane,
)


def test_default_fallback_prefers_cheapest_deterministic_lane():
    decision = choose_next_lane(policy=AcquisitionFallbackPolicy())
    assert decision.lane is not None
    assert decision.lane.name == "static_fetch"
    assert decision.attempts_remaining == 2
    assert decision.cost_remaining == 5


def test_fallback_skips_failed_and_unauthorized_lanes():
    lanes = (
        AcquisitionLane("static", AcquisitionLaneKind.STATIC_FETCH, "static", 1, authorized=False, priority=1),
        AcquisitionLane("structured", AcquisitionLaneKind.STRUCTURED_DATA, "structured", 1, priority=2),
        AcquisitionLane("search", AcquisitionLaneKind.SEARCH_DISCOVERY, "search", 2, evidence_capable=False, priority=3),
    )
    decision = choose_next_lane(
        policy=AcquisitionFallbackPolicy(max_attempts=3, max_cost_units=4),
        failed_lanes=("structured",),
        lanes=lanes,
    )
    assert decision.lane is not None
    assert decision.lane.name == "search"


def test_search_discovery_never_claims_evidence_capability():
    decision = choose_next_lane(
        policy=AcquisitionFallbackPolicy(allowed_capabilities=("search",)),
    )
    assert decision.lane is not None
    assert decision.lane.kind is AcquisitionLaneKind.SEARCH_DISCOVERY
    assert decision.lane.evidence_capable is False


def test_browser_escalation_requires_explicit_permission_and_budget():
    denied = choose_next_lane(
        policy=AcquisitionFallbackPolicy(max_attempts=4, max_cost_units=5, allow_browser=False),
        failed_lanes=("static_fetch", "structured_data", "search_discovery"),
    )
    assert denied.terminal_reason is AcquisitionOutcome.BUDGET_EXHAUSTED

    allowed = choose_next_lane(
        policy=AcquisitionFallbackPolicy(max_attempts=4, max_cost_units=6, allow_browser=True),
        failed_lanes=("static_fetch", "structured_data", "search_discovery"),
    )
    assert allowed.lane is not None
    assert allowed.lane.name == "browser"
    assert allowed.cost_remaining == 1


def test_cost_and_attempt_bounds_fail_closed():
    exhausted_attempts = choose_next_lane(
        policy=AcquisitionFallbackPolicy(),
        attempts_used=3,
    )
    assert exhausted_attempts.terminal_reason is AcquisitionOutcome.BUDGET_EXHAUSTED

    exhausted_cost = choose_next_lane(
        policy=AcquisitionFallbackPolicy(),
        cost_used=6,
    )
    assert exhausted_cost.terminal_reason is AcquisitionOutcome.BUDGET_EXHAUSTED

    no_fit = choose_next_lane(
        policy=AcquisitionFallbackPolicy(max_attempts=4, max_cost_units=2, allow_browser=True),
        failed_lanes=("static_fetch", "structured_data", "search_discovery"),
    )
    assert no_fit.terminal_reason is AcquisitionOutcome.BUDGET_EXHAUSTED


def test_capability_and_lane_validation_are_strict():
    with pytest.raises(ValueError):
        AcquisitionLane("", AcquisitionLaneKind.STATIC_FETCH, "static", 1).validate()
    with pytest.raises(ValueError):
        AcquisitionLane("bad", AcquisitionLaneKind.BROWSER, "browser", 1, requires_browser=False).validate()
    with pytest.raises(ValueError):
        AcquisitionLane("bad", AcquisitionLaneKind.STATIC_FETCH, "static", 0).validate()
    with pytest.raises(ValueError):
        AcquisitionFallbackPolicy(max_attempts=0).validate()
    with pytest.raises(ValueError):
        AcquisitionFallbackPolicy(max_cost_units=0).validate()
    with pytest.raises(ValueError):
        AcquisitionFallbackPolicy(allowed_capabilities=("",)).validate()


def test_runtime_counters_must_be_non_negative():
    with pytest.raises(ValueError):
        choose_next_lane(policy=AcquisitionFallbackPolicy(), attempts_used=-1)
    with pytest.raises(ValueError):
        choose_next_lane(policy=AcquisitionFallbackPolicy(), cost_used=-1)
