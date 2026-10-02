#!/usr/bin/env python3
"""Deterministic coverage gate for the repository-wide CrossFire automation contract."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

EXPECTED_LENSES = ("structure", "boundary", "runtime", "security", "quality", "provenance")
EXPECTED_AI_COUNTS = (0, 2, 4, 6)


def fail(message: str, errors: list[str]) -> None:
    errors.append(message)


def validate(root: Path) -> dict[str, object]:
    errors: list[str] = []
    matrix_path = root / "docs" / "PROJECT_IMPROVEMENT_MATRIX.json"
    policy_path = root / "docs" / "CROSSFIRE_AUTOMATION_POLICY.json"
    if not matrix_path.is_file():
        return {"schema": "crossfire-surface-audit/v1", "passed": False, "errors": ["project improvement matrix missing"]}
    if not policy_path.is_file():
        return {"schema": "crossfire-surface-audit/v1", "passed": False, "errors": ["crossfire automation policy missing"]}
    try:
        matrix = json.loads(matrix_path.read_text(encoding="utf-8"))
        policy = json.loads(policy_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return {"schema": "crossfire-surface-audit/v1", "passed": False, "errors": [f"JSON invalid: {exc}"]}

    if policy.get("schema") != "crossfire-automation-policy/v1":
        fail("crossfire automation policy schema invalid", errors)
    if policy.get("target_ai_lanes") != 6:
        fail("target_ai_lanes must be 6", errors)
    if policy.get("strong_ai_lane_threshold") != 5:
        fail("strong_ai_lane_threshold must be 5", errors)
    if tuple(policy.get("adaptive_ai_lane_counts", ())) != EXPECTED_AI_COUNTS:
        fail("adaptive_ai_lane_counts must be 0/2/4/6", errors)
    if tuple(policy.get("deterministic_lenses", ())) != EXPECTED_LENSES:
        fail("deterministic_lenses must be structure/boundary/runtime/security/quality/provenance", errors)
    for key in ("independence", "lane_failure_isolation", "mutations_after_evidence_only"):
        if policy.get(key) is not True:
            fail(f"crossfire policy {key} must be true", errors)
    if policy.get("shared_result_feedback") is not False:
        fail("crossfire policy shared_result_feedback must be false", errors)
    if policy.get("raw_ai_output") != "excluded_by_default":
        fail("raw_ai_output must be excluded_by_default", errors)
    if policy.get("authority") != "existing_canonical_deterministic_or_policy_runtime":
        fail("AI authority must remain existing canonical deterministic/policy runtime", errors)

    components = matrix.get("components")
    if not isinstance(components, dict) or not components:
        fail("components missing", errors)
        components = {}

    declared_components = sorted(str(x) for x in policy.get("covered_components", ()))
    matrix_components = sorted(str(x) for x in components)
    if declared_components and declared_components != matrix_components:
        fail("policy covered_components do not exactly match project-improvement components", errors)
    elif not declared_components:
        fail("policy covered_components missing", errors)

    missing_workflows: dict[str, list[str]] = {}
    for name, component in components.items():
        if not isinstance(component, dict):
            fail(f"component {name} is not an object", errors)
            continue
        workflows = component.get("workflows")
        if not isinstance(workflows, list) or not workflows:
            missing_workflows[name] = ["<at least one workflow>"]
            continue
        absent = [wf for wf in workflows if not (root / ".github" / "workflows" / str(wf)).is_file()]
        if absent:
            missing_workflows[name] = absent
    for name, paths in missing_workflows.items():
        fail(f"component {name} references missing workflow(s): {', '.join(paths)}", errors)

    required_workflows = tuple(policy.get("required_automation_surfaces", ()))
    absent_required = [p for p in required_workflows if not (root / p).is_file()]
    if absent_required:
        fail("required CrossFire automation workflow(s) missing: " + ", ".join(absent_required), errors)

    return {
        "schema": "crossfire-surface-audit/v1",
        "passed": not errors,
        "component_count": len(components),
        "covered_components": matrix_components if declared_components == matrix_components else declared_components,
        "missing_workflows": missing_workflows,
        "required_workflows": list(required_workflows),
        "policy": {
            "target_ai_lanes": policy.get("target_ai_lanes"),
            "strong_ai_lane_threshold": policy.get("strong_ai_lane_threshold"),
            "adaptive_ai_lane_counts": policy.get("adaptive_ai_lane_counts"),
            "deterministic_lenses": policy.get("deterministic_lenses"),
            "independence": policy.get("independence"),
            "shared_result_feedback": policy.get("shared_result_feedback"),
        },
        "errors": errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = validate(args.root.resolve())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
