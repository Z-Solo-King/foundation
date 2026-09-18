import pytest

from backend.execution.stop_decision import (
    StopDecisionReason,
    StopDecisionSnapshot,
    decide_continuation,
)


def test_required_evidence_overrides_low_marginal_value():
    decision = decide_continuation(
        StopDecisionSnapshot(
            required_missing=1,
            source_novelty_milli=10,
            remaining_resource_units=5,
            remaining_ms=5000,
        )
    )
    assert decision.continue_research is True
    assert decision.reason is StopDecisionReason.REQUIRED_EVIDENCE_MISSING
    assert decision.marginal_value_milli == 1000
    assert len(decision.fingerprint) == 64


def test_contradiction_and_freshness_require_more_work():
    contradiction = decide_continuation(
        StopDecisionSnapshot(
            unresolved_contradictions=1,
            remaining_resource_units=2,
            remaining_ms=100,
        )
    )
    freshness = decide_continuation(
        StopDecisionSnapshot(
            freshness_noncompliant=1,
            remaining_resource_units=2,
            remaining_ms=100,
        )
    )
    assert contradiction.reason is StopDecisionReason.CONTRADICTION_REQUIRES_INVESTIGATION
    assert freshness.reason is StopDecisionReason.FRESHNESS_REQUIRES_REFRESH


def test_novel_evidence_continues_with_recorded_value():
    decision = decide_continuation(
        StopDecisionSnapshot(
            source_novelty_milli=450,
            independent_corroboration=1,
            remaining_resource_units=5,
            remaining_ms=500,
        )
    )
    assert decision.continue_research is True
    assert decision.reason is StopDecisionReason.NOVEL_EVIDENCE_WORTH_COST
    assert decision.marginal_value_milli == 450


def test_budget_deadline_and_lane_fail_closed_first():
    assert decide_continuation(StopDecisionSnapshot(required_missing=1)).reason is StopDecisionReason.BUDGET_EXHAUSTED
    assert decide_continuation(StopDecisionSnapshot(remaining_resource_units=1, remaining_ms=0)).reason is StopDecisionReason.DEADLINE_EXCEEDED
    assert decide_continuation(StopDecisionSnapshot(remaining_resource_units=1, remaining_ms=1, acquisition_available=False)).reason is StopDecisionReason.NO_ACQUISITION_LANE


def test_redundant_and_sufficient_paths_stop():
    redundant = decide_continuation(
        StopDecisionSnapshot(
            independent_corroboration=0,
            remaining_resource_units=1,
            remaining_ms=1,
        )
    )
    sufficient = decide_continuation(
        StopDecisionSnapshot(
            independent_corroboration=2,
            remaining_resource_units=1,
            remaining_ms=1,
        )
    )
    assert redundant.reason is StopDecisionReason.REDUNDANT_EVIDENCE
    assert sufficient.reason is StopDecisionReason.SUFFICIENT_COVERAGE
    assert redundant.continue_research is False
    assert sufficient.continue_research is False


def test_snapshot_validation_rejects_negative_and_invalid_values():
    with pytest.raises(ValueError):
        StopDecisionSnapshot(required_missing=-1).validate()
    with pytest.raises(ValueError):
        StopDecisionSnapshot(source_novelty_milli=1001).validate()
    with pytest.raises(ValueError):
        StopDecisionSnapshot(remaining_ms=-1).validate()


def test_identical_snapshots_have_stable_decision_fingerprint():
    snapshot = StopDecisionSnapshot(
        source_novelty_milli=200,
        independent_corroboration=1,
        remaining_resource_units=3,
        remaining_ms=100,
    )
    assert decide_continuation(snapshot).fingerprint == decide_continuation(snapshot).fingerprint
