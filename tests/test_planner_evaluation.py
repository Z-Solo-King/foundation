import pytest

from backend.intelligence.planner_evaluation import (
    PlannerMetrics,
    candidate_improves,
    evidence_gain_per_unit,
    quality_non_regression,
    research_regret,
    safe_region,
)


def test_candidate_must_stay_inside_quality_floor():
    baseline = PlannerMetrics(task_coverage=.8, claim_coverage=.8, retrieval_recall=.8, evidence_gain_per_unit=.5)
    candidate = PlannerMetrics(task_coverage=.85, claim_coverage=.82, retrieval_recall=.81, evidence_gain_per_unit=.6)
    assert safe_region(candidate, {"task_coverage": .8, "claim_coverage": .8, "retrieval_recall": .8})
    assert quality_non_regression(baseline, candidate)
    assert candidate_improves(baseline, candidate, {"task_coverage": .8, "claim_coverage": .8, "retrieval_recall": .8})


def test_lower_quality_is_not_saved_by_efficiency():
    baseline = PlannerMetrics(task_coverage=.9, claim_coverage=.9, retrieval_recall=.9, latency=10, resource_consumption=10)
    candidate = PlannerMetrics(task_coverage=.7, claim_coverage=.95, retrieval_recall=.95, latency=1, resource_consumption=1)
    assert not quality_non_regression(baseline, candidate)
    assert not candidate_improves(baseline, candidate, {"task_coverage": .85, "claim_coverage": .85, "retrieval_recall": .85})


def test_single_quality_regression_blocks_promotion_even_when_other_metrics_gain():
    baseline = PlannerMetrics(
        task_coverage=.9, claim_coverage=.9, retrieval_recall=.9,
        citation_entailment=.9, primary_source_coverage=.9,
        independent_origin_coverage=.9, contradiction_recall=.9,
        freshness=.9, evidence_gain_per_unit=.5,
    )
    candidate = PlannerMetrics(
        task_coverage=.91, claim_coverage=.91, retrieval_recall=.92,
        citation_entailment=.89, primary_source_coverage=.93,
        independent_origin_coverage=.91, contradiction_recall=.92,
        freshness=.91, evidence_gain_per_unit=.8,
    )
    assert not quality_non_regression(baseline, candidate)
    assert not candidate_improves(baseline, candidate, {"task_coverage": .8})


def test_research_regret_and_evidence_gain_are_bounded_and_fail_closed():
    assert research_regret(.7, .9) == pytest.approx(.2)
    assert research_regret(.9, .7) == 0.0
    assert evidence_gain_per_unit(5, 2) == pytest.approx(2.5)
    assert evidence_gain_per_unit(5, 0) == 5
    with pytest.raises(ValueError): research_regret(-.1, .5)
    with pytest.raises(ValueError): research_regret(.5, 1.1)
    with pytest.raises(ValueError): evidence_gain_per_unit(-1, 1)
    with pytest.raises(ValueError): evidence_gain_per_unit(1, -1)