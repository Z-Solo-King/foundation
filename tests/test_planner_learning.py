from backend.intelligence.source_profiles import MethodObservation, SourceProfile, update_profile
from backend.intelligence.strategy_evaluation import StrategyExperiment, StrategyMetrics, candidate_beats_baseline


def metrics(**overrides):
    base = dict(correctness=.9, evidence_quality=.9, citation_alignment=.9, independence=.9,
                freshness=.9, latency=.5, failure_rate=.1, resource_cost=.5)
    base.update(overrides)
    return StrategyMetrics(**base)


def test_source_profile_learning_is_sample_guarded():
    profile = SourceProfile(source_id="s", source_family="official")
    updated = update_profile(profile, MethodObservation("api", True, completeness=1.0, observed_at="t1"))
    assert updated.sample_size == 1
    assert updated.preferred_method == "api"
    assert updated.success_by_method["api"] > .5


def test_candidate_requires_multi_metric_non_regression():
    exp = StrategyExperiment("e", "base", "cand", "corpus", metrics(latency=.4, resource_cost=.4), metrics())
    assert candidate_beats_baseline(exp)


def test_candidate_rejected_for_correctness_regression():
    exp = StrategyExperiment("e", "base", "cand", "corpus", metrics(correctness=.8, latency=.3), metrics())
    assert not candidate_beats_baseline(exp)
