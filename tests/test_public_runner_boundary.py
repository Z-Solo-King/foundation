from __future__ import annotations

import json
from pathlib import Path

import pytest

from benchmark.public_runner_boundary import validate_jsonl


def _record(**overrides: object) -> dict[str, object]:
    record = {
        "schema": "nightly-research-program/v1",
        "program_id": "lane0-slot0",
        "lane": 0,
        "slot": 0,
        "status": "completed",
        "measurement": {
            "allocated_agents": 6,
            "completed_agents": 6,
            "failed_agents": 0,
            "wall_clock_seconds": 1.25,
            "agent_seconds": 2.5,
            "useful_findings": 1,
            "unique_sources": 1,
            "duplicate_rate": 0.0,
            "answer_quality_0_to_10": None,
            "follow_up_questions": 0,
        },
        "findings": [{
            "claim": "A public-safe finding",
            "source_url": "https://example.com/source",
            "source_family": "web",
            "acquisition_method": "direct",
            "evidence_status": "candidate",
        }],
    }
    record.update(overrides)
    return record


def test_valid_public_research_artifact(tmp_path: Path) -> None:
    path = tmp_path / "lane.jsonl"
    path.write_text(json.dumps(_record()) + "\n", encoding="utf-8")
    report = validate_jsonl(path, expected_lane=0)
    assert report["schema"] == "public-research-artifact-validation/v1"
    assert report["records"] == 1


def test_rejects_private_agent_fields(tmp_path: Path) -> None:
    record = _record()
    record["agent_notes"] = "secret execution detail"  # type: ignore[index]
    path = tmp_path / "lane.jsonl"
    path.write_text(json.dumps(record) + "\n", encoding="utf-8")
    with pytest.raises(ValueError, match="non-public fields"):
        validate_jsonl(path, expected_lane=0)


def test_rejects_credential_like_text(tmp_path: Path) -> None:
    record = _record()
    record["findings"][0]["claim"] = "api_key=super-secret"  # type: ignore[index]
    path = tmp_path / "lane.jsonl"
    path.write_text(json.dumps(record) + "\n", encoding="utf-8")
    with pytest.raises(ValueError, match="credential material"):
        validate_jsonl(path, expected_lane=0)


def test_rejects_private_source_host(tmp_path: Path) -> None:
    record = _record()
    record["findings"][0]["source_url"] = "http://127.0.0.1/private"  # type: ignore[index]
    path = tmp_path / "lane.jsonl"
    path.write_text(json.dumps(record) + "\n", encoding="utf-8")
    with pytest.raises(ValueError, match="private/local host"):
        validate_jsonl(path, expected_lane=0)


def test_rejects_schema_and_duplicate_programs(tmp_path: Path) -> None:
    first = _record()
    second = _record()
    second["schema"] = "private-agent/v1"
    path = tmp_path / "lane.jsonl"
    path.write_text(json.dumps(first) + "\n" + json.dumps(second) + "\n", encoding="utf-8")
    with pytest.raises(ValueError, match="unsupported public research schema"):
        validate_jsonl(path, expected_lane=0)


def test_rejects_nested_execution_context(tmp_path: Path) -> None:
    record = _record()
    record["measurement"]["execution_context"] = {"prompt": "private"}  # type: ignore[index]
    path = tmp_path / "lane.jsonl"
    path.write_text(json.dumps(record) + "\n", encoding="utf-8")
    with pytest.raises(ValueError, match="measurement contains non-public fields"):
        validate_jsonl(path, expected_lane=0)
