from __future__ import annotations

import json
from pathlib import Path

from benchmark.ai_agent_benchmark_contract import (
    OBSERVATION_SCHEMA,
    validate_manifest,
    validate_observation_envelope,
)

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
        "observation": {},
    }
    assert validate_observation_envelope(envelope) == []
