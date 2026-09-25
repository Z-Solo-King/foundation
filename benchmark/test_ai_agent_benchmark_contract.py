from __future__ import annotations

import json
from pathlib import Path

from benchmark.ai_agent_benchmark_contract import (
    OBSERVATION_SCHEMA,
    validate_manifest,
    validate_observation_envelope,
)
from benchmark.aggregate_ai_agent_benchmark import aggregate

ROOT = Path(__file__).resolve().parents[1]


def test_ai_agent_benchmark_manifest_is_valid() -> None:
    payload = json.loads((ROOT / "benchmark" / "ai_agent_task_matrix_v1.json").read_text(encoding="utf-8"))
    assert validate_manifest(payload) == []


def test_ai_agent_observation_envelope_is_valid() -> None:
    schema = json.loads((ROOT / "benchmark" / "ai_agent_observation.schema.json").read_text(encoding="utf-8"))
    assert schema["properties"]["schema"]["const"] == OBSERVATION_SCHEMA
    envelope = {
        "schema": OBSERVATION_SCHEMA,
        "run_id": "test-run",
        "provider": "test-provider",
        "model": "test-model",
        "agent_role": "explorer",
        "lane": "A",
        "task_id": "ai-a-01",
        "fixture_version": "v1",
        "repository_revision": "test-sha",
        "tool_policy_version": "v1",
        "evidence_tier": "R1",
        "observation": {
            "run_id": "test-run",
            "provider": "test-provider",
            "model": "test-model",
            "task_id": "ai-a-01",
        },
    }
    # The inner scorer observation requires all counters, so complete it explicitly.
    envelope["observation"].update({
        "input_tokens": 100,
        "output_tokens": 50,
        "thinking_tokens": 20,
        "cached_tokens": 30,
        "tool_calls": 4,
        "useful_tool_calls": 4,
        "relevant_sources": 2,
        "sources_used": 2,
        "files_read": 3,
        "duplicate_actions": 0,
        "irrelevant_actions": 0,
        "compaction_events": 0,
        "context_peak_tokens": 120,
        "required_claims": 2,
        "supported_claims": 2,
        "correct_claims": 2,
        "missed_requirements": 0,
        "unsupported_claims": 0,
        "self_corrections": 1,
        "successful_actions": 2,
    })
    assert validate_observation_envelope(envelope) == []


def test_ai_agent_observation_aggregation_reuses_existing_scorer() -> None:
    observation = {
        "run_id": "test-run",
        "provider": "test-provider",
        "model": "test-model",
        "task_id": "ai-a-01",
        "input_tokens": 100,
        "output_tokens": 50,
        "thinking_tokens": 20,
        "cached_tokens": 30,
        "tool_calls": 4,
        "useful_tool_calls": 4,
        "relevant_sources": 2,
        "sources_used": 2,
        "files_read": 3,
        "duplicate_actions": 0,
        "irrelevant_actions": 0,
        "compaction_events": 0,
        "context_peak_tokens": 120,
        "required_claims": 2,
        "supported_claims": 2,
        "correct_claims": 2,
        "missed_requirements": 0,
        "unsupported_claims": 0,
        "self_corrections": 1,
        "successful_actions": 2,
    }
    envelope = {
        "schema": OBSERVATION_SCHEMA,
        "run_id": "test-run",
        "provider": "test-provider",
        "model": "test-model",
        "agent_role": "explorer",
        "lane": "A",
        "task_id": "ai-a-01",
        "fixture_version": "v1",
        "repository_revision": "test-sha",
        "tool_policy_version": "v1",
        "evidence_tier": "R1",
        "artifact_digest": "test-digest",
        "observation": observation,
    }
    report = aggregate([envelope, {**envelope, "run_id": "test-run-2", "observation": {**observation, "run_id": "test-run-2"}}])
    assert report["observations"] == 2
    assert report["models"]["test-model"]["runs"] == 2
    assert report["roles"]["explorer"]["runs"] == 2
    assert report["lanes"]["A"]["runs"] == 2
