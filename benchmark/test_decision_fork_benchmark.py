from __future__ import annotations

from dataclasses import replace

import pytest

from benchmark.decision_fork_benchmark import (
    DecisionForkObservation,
    aggregate_decision_forks,
    score_decision_fork,
)


def _observation(chosen: str = "search") -> DecisionForkObservation:
    return DecisionForkObservation(
        run_id="run-1",
        task_id="task-1",
        trajectory_id="trajectory-1",
        fork_id="fork-1",
        state_digest="sha256:state",
        decision_type="route",
        candidates=("search", "code", "review"),
        chosen_candidate=chosen,
        hindsight_best_candidate="search",
        outcome_visible_to_decider=False,
        provider="test",
        model="fixture",
        decision_latency_ms=12.5,
        decision_calls=1,
    )


def test_decision_fork_correctness_is_deterministic() -> None:
    result = score_decision_fork(_observation())
    assert result["decision_correct"] is True
    assert result["decision_accuracy"] == 1.0
    assert result["normalized_rank_distance"] == 0.0


def test_decision_fork_wrong_choice_retains_regret_signal() -> None:
    result = score_decision_fork(_observation("review"))
    assert result["decision_correct"] is False
    assert result["decision_accuracy"] == 0.0
    assert result["normalized_rank_distance"] == 1.0


def test_aggregate_keeps_each_fork_observable() -> None:
    report = aggregate_decision_forks([_observation(), _observation("code")])
    assert report["observations"] == 2
    assert report["correct_observations"] == 1
    assert report["decision_accuracy"] == 0.5
    assert len(report["forks"]) == 2


def test_outcome_visibility_is_never_allowed() -> None:
    with pytest.raises(ValueError, match="post-fork outcome"):
        replace(_observation(), outcome_visible_to_decider=True)


def test_invalid_candidate_choice_is_rejected() -> None:
    with pytest.raises(ValueError, match="chosen_candidate"):
        replace(_observation(), chosen_candidate="deploy")
