import pytest

from backend.intelligence.source_profiles import MethodObservation, SourceProfile, update_profile
from backend.intelligence.strategy_evaluation import (
    StrategyExperiment,
    StrategyLifecycle,
    StrategyMetrics,
    StrategyStage,
    candidate_beats_baseline,
    enter_canary,
    mark_promotable,
    mark_promoted,
    rollback,
)


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


def test_shadow_canary_promotable_promoted_and_rollback_flow():
    exp = StrategyExperiment("e1", "base", "cand", "corpus", metrics(latency=.4, resource_cost=.4), metrics())
    lifecycle = StrategyLifecycle("cand", "v1")
    canary = enter_canary(lifecycle, exp, .05)
    assert canary.stage is StrategyStage.CANARY
    assert canary.last_experiment_id == "e1"
    promotable = mark_promotable(canary, exp)
    assert promotable.stage is StrategyStage.PROMOTABLE
    promoted = mark_promoted(promotable)
    assert promoted.stage is StrategyStage.PROMOTED
    assert promoted.canary_fraction == 1.0
    rolled = rollback(promoted, "quality regression")
    assert rolled.stage is StrategyStage.ROLLBACK
    assert rolled.rollback_reason == "quality regression"


def test_strategy_lifecycle_rejects_invalid_transitions_and_values():
    with pytest.raises(ValueError): StrategyLifecycle("", "v1").validate()
    with pytest.raises(ValueError): StrategyLifecycle("s", "v1", canary_fraction=1.1).validate()
    with pytest.raises(ValueError): StrategyLifecycle("s", "v1", StrategyStage.ROLLBACK).validate()
    lifecycle = StrategyLifecycle("s", "v1")
    exp = StrategyExperiment("e", "base", "cand", "corpus", metrics(correctness=.8), metrics())
    with pytest.raises(ValueError): enter_canary(lifecycle, exp, .1)
    good = StrategyExperiment("e", "base", "cand", "corpus", metrics(latency=.4, resource_cost=.4), metrics())
    with pytest.raises(ValueError): enter_canary(lifecycle, good, 0)
    canary = enter_canary(lifecycle, good, .1)
    with pytest.raises(ValueError): mark_promotable(lifecycle, good)
    bad_canary = StrategyExperiment("e2", "base", "cand", "corpus", metrics(correctness=.8), metrics())
    with pytest.raises(ValueError): mark_promotable(canary, bad_canary)
    with pytest.raises(ValueError): mark_promoted(canary)
    with pytest.raises(ValueError): rollback(canary, "")


def test_strategy_lifecycle_validation_and_candidate_gate_edges():
    with pytest.raises(ValueError): StrategyLifecycle("s", "v1", StrategyStage.ROLLBACK, rollback_reason="").validate()
    lifecycle = StrategyLifecycle("s", "v1", StrategyStage.CANARY, canary_fraction=.1)
    with pytest.raises(ValueError): enter_canary(lifecycle, good := StrategyExperiment("e", "b", "c", "f", metrics(), metrics()), .1)
    unregistered = StrategyExperiment("e", "b", "c", "f", metrics(), metrics(), pre_registered=False)
    assert not candidate_beats_baseline(unregistered)
    with pytest.raises(ValueError): enter_canary(StrategyLifecycle("s", "v1"), good, 1.1)
    with pytest.raises(ValueError): rollback(StrategyLifecycle("s", "v1"), " ")
