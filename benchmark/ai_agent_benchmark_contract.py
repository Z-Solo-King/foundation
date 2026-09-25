"""Validation helpers for the project-native AI/agent benchmark manifest and observation envelope."""
from __future__ import annotations

from collections import Counter
import json
from pathlib import Path
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parent
OBSERVATION_SCHEMA = "heroic-ai-agent-benchmark-observation/v1"
ROLES = {"main", "explorer", "worker", "researcher", "advisor"}
LANES = {"A", "B", "C", "D", "E", "F"}


def validate_manifest(payload: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    if payload.get("schema") != "ai-agent-benchmark-task-matrix/v1":
        errors.append("unexpected schema")
    tasks = payload.get("tasks")
    lanes = payload.get("lanes")
    weights = payload.get("scoring_dimensions")
    if not isinstance(tasks, list) or not tasks:
        return errors + ["tasks must be a non-empty list"]
    if not isinstance(lanes, list) or len(lanes) != 6:
        errors.append("exactly six benchmark lanes are required")
    if not isinstance(weights, list) or not weights:
        errors.append("scoring_dimensions must be non-empty")
    else:
        total = sum(float(x.get("weight", 0)) for x in weights if isinstance(x, Mapping))
        if abs(total - 1.0) > 1e-9:
            errors.append(f"scoring weights must sum to 1.0, got {total}")
    ids = [t.get("task_id") for t in tasks if isinstance(t, Mapping)]
    for task_id, count in Counter(ids).items():
        if count != 1:
            errors.append(f"duplicate task_id: {task_id}")
    if len(tasks) != 24:
        errors.append(f"expected 24 tasks, got {len(tasks)}")
    lane_codes = {x.get("code") for x in lanes if isinstance(x, Mapping)}
    if lane_codes != LANES:
        errors.append(f"lane codes must be exactly {sorted(LANES)}, got {sorted(lane_codes)}")
    for task in tasks:
        if not isinstance(task, Mapping):
            errors.append("task entry is not an object")
            continue
        if task.get("lane") not in lane_codes:
            errors.append(f"unknown lane for {task.get('task_id')}")
        if task.get("repeat_count") != 3:
            errors.append(f"repeat_count must be 3 for {task.get('task_id')}")
        required = set(task.get("required_checks", []))
        for check in ("canonical_owner", "exact_revision", "evidence_ladder", "no_unsupported_completion_claim"):
            if check not in required:
                errors.append(f"missing required check {check} for {task.get('task_id')}")
        roles = task.get("agent_roles")
        if not isinstance(roles, list) or not roles or not set(roles).issubset(ROLES):
            errors.append(f"invalid agent_roles for {task.get('task_id')}")
    return errors


def validate_observation_envelope(payload: Mapping[str, Any]) -> list[str]:
    required = {
        "schema", "run_id", "provider", "model", "agent_role", "lane", "task_id",
        "fixture_version", "repository_revision", "tool_policy_version",
        "evidence_tier", "observation"
    }
    errors = [f"missing observation field: {key}" for key in sorted(required - set(payload))]
    if payload.get("schema") != OBSERVATION_SCHEMA:
        errors.append("unexpected observation schema")
    if payload.get("agent_role") not in ROLES:
        errors.append("invalid agent_role")
    if payload.get("lane") not in LANES:
        errors.append("invalid lane")
    for key in ("run_id", "provider", "model", "task_id", "fixture_version", "repository_revision", "tool_policy_version", "evidence_tier"):
        if key in payload and (not isinstance(payload[key], str) or not payload[key].strip()):
            errors.append(f"{key} must be a non-empty string")
    if not isinstance(payload.get("observation"), Mapping):
        errors.append("observation must be an object")
    return errors


def main() -> int:
    matrix = json.loads((ROOT / "ai_agent_task_matrix_v1.json").read_text(encoding="utf-8"))
    schema = json.loads((ROOT / "ai_agent_observation.schema.json").read_text(encoding="utf-8"))
    errors = validate_manifest(matrix)
    if schema.get("properties", {}).get("schema", {}).get("const") != OBSERVATION_SCHEMA:
        errors.append("observation schema constant mismatch")
    print(json.dumps({"status": "PASS" if not errors else "FAIL", "errors": errors}, indent=2))
    return 0 if not errors else 1
