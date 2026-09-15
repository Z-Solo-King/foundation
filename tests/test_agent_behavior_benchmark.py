from __future__ import annotations

import pytest

from benchmark.agent_behavior_benchmark import (
    AgentRunObservation,
    compare_models,
    compare_scores,
    load_observation,
    score_run,
)


def base_run(**overrides: int | str) -> AgentRunObservation:
    values: dict[str, int | str] = {
        "run_id": "run-1",
        "provider": "test",
        "model": "model-a",
        "task_id": "task-1",
        "input_tokens": 1000,
        "output_tokens": 500,
        "thinking_tokens": 500,
        "cached_tokens": 1000,
        "tool_calls": 4,
        "useful_tool_calls": 3,
        "relevant_sources": 3,
        "sources_used": 3,
        "files_read": 2,
        "duplicate_actions": 0,
        "irrelevant_actions": 0,
        "compaction_events": 0,
        "context_peak_tokens": 1200,
        "required_claims": 4,
        "supported_claims": 4,
        "correct_claims": 4,
        "missed_requirements": 0,
        "unsupported_claims": 0,
        "self_corrections": 1,
        "successful_actions": 4,
    }
    values.update(overrides)
    return AgentRunObservation(**values)


def test_score_is_bounded_and_deterministic() -> None:
    first = score_run(base_run())
    second = score_run(base_run())
    assert first == second
    for value in first.to_dict().values():
        if isinstance(value, float):
            assert 0.0 <= value <= 1.0


def test_bad_run_loses_precision_and_correctness() -> None:
    good = score_run(base_run())
    bad = score_run(
        base_run(
            correct_claims=2,
            supported_claims=1,
            missed_requirements=2,
            unsupported_claims=3,
            duplicate_actions=3,
            irrelevant_actions=3,
        )
    )
    assert bad.correctness < good.correctness
    assert bad.precision < good.precision
    assert bad.overall < good.overall


def test_compare_models_groups_by_model() -> None:
    result = compare_models([base_run(model="a"), base_run(run_id="run-2", model="b")])
    assert set(result["models"]) == {"a", "b"}
    assert result["models"]["a"]["runs"] == 1


def test_compare_scores_orders_best_first() -> None:
    better = score_run(base_run())
    worse = score_run(base_run(correct_claims=1, supported_claims=1, missed_requirements=3))
    assert compare_scores([worse, better])[0] == better


def test_negative_counts_and_empty_identity_are_rejected() -> None:
    with pytest.raises(ValueError):
        base_run(tool_calls=-1)
    with pytest.raises(ValueError):
        base_run(model=" ")


def test_json_compatible_loader() -> None:
    observation = load_observation({"run_id": "x", "provider": "p", "model": "m", "task_id": "t"})
    assert observation.run_id == "x"
