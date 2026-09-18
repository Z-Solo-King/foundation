import pytest

from backend.sources.fallbacks import (
    AcquisitionDecisionCode,
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
        AcquisitionLane("bad", AcquisitionLaneKind.STATIC_FETCH, "static", 1, requires_browser=True).validate()
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


def test_fallback_decision_is_versioned_and_deterministically_fingerprinted():
    policy = AcquisitionFallbackPolicy(revision="policy-7")
    first = choose_next_lane(policy=policy)
    second = choose_next_lane(policy=policy)
    assert first.decision_code is AcquisitionDecisionCode.READY
    assert first.policy_revision == "policy-7"
    assert first.digest == second.digest
    assert first.to_dict()["schema"] == "acquisition-fallback-decision/v1"


def test_fallback_classifies_attempt_and_cost_exhaustion():
    assert choose_next_lane(
        policy=AcquisitionFallbackPolicy(max_attempts=1),
        attempts_used=1,
    ).decision_code is AcquisitionDecisionCode.ATTEMPTS_EXHAUSTED
    assert choose_next_lane(
        policy=AcquisitionFallbackPolicy(max_cost_units=1),
        cost_used=1,
    ).decision_code is AcquisitionDecisionCode.COST_EXHAUSTED


def test_fallback_classifies_no_budget_fit_separately():
    lanes = (
        AcquisitionLane("cheap", AcquisitionLaneKind.STATIC_FETCH, "static", 3, priority=1),
    )
    decision = choose_next_lane(
        policy=AcquisitionFallbackPolicy(max_attempts=3, max_cost_units=2),
        lanes=lanes,
    )
    assert decision.decision_code is AcquisitionDecisionCode.NO_BUDGET_FIT


def test_fallback_policy_revision_is_required():
    with pytest.raises(ValueError, match="revision"):
        AcquisitionFallbackPolicy(revision="").validate()
