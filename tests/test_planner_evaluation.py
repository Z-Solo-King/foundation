from backend.intelligence.planner_evaluation import PlannerMetrics, candidate_improves, safe_region


def test_candidate_must_stay_inside_quality_floor():
    baseline = PlannerMetrics(task_coverage=.8, claim_coverage=.8, retrieval_recall=.8, evidence_gain_per_unit=.5)
    candidate = PlannerMetrics(task_coverage=.85, claim_coverage=.82, retrieval_recall=.81, evidence_gain_per_unit=.6)
    assert safe_region(candidate, {"task_coverage": .8, "claim_coverage": .8, "retrieval_recall": .8})
    assert candidate_improves(baseline, candidate, {"task_coverage": .8, "claim_coverage": .8, "retrieval_recall": .8})


def test_lower_quality_is_not_saved_by_efficiency():
    baseline = PlannerMetrics(task_coverage=.9, claim_coverage=.9, retrieval_recall=.9, latency=10, resource_consumption=10)
    candidate = PlannerMetrics(task_coverage=.7, claim_coverage=.95, retrieval_recall=.95, latency=1, resource_consumption=1)
    assert not candidate_improves(baseline, candidate, {"task_coverage": .85, "claim_coverage": .85, "retrieval_recall": .85})
