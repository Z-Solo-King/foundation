#!/usr/bin/env python3
"""Fail-closed cross-repository cohesion validator."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "docs" / "SYSTEM_INTEGRATION_CONTRACT.json"
MATRIX = ROOT / "docs" / "PROJECT_IMPROVEMENT_MATRIX.json"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def require_text(path: Path, needles: list[str], errors: list[str], label: str) -> None:
    if not path.is_file():
        errors.append(f"{label}:missing")
        return
    text = path.read_text(encoding="utf-8", errors="ignore")
    for needle in needles:
        if needle not in text:
            errors.append(f"{label}:missing-anchor:{needle}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--foundation-root", type=Path, required=True)
    parser.add_argument("--operations-root", type=Path)
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()

    errors: list[str] = []
    foundation = args.foundation_root.resolve()
    operations = args.operations_root.resolve() if args.operations_root else None

    contract = load(foundation / "docs" / CONTRACT.name)
    matrix = load(foundation / "docs" / MATRIX.name)

    if contract.get("schema_version") != "system-integration-contract/v1":
        errors.append("contract schema mismatch")
    if matrix.get("system_integration_contract") != "docs/SYSTEM_INTEGRATION_CONTRACT.json":
        errors.append("project matrix not bound to integration contract")

    controls = matrix.get("cross_cutting_controls", {})
    required_controls = set(contract.get("cross_cutting_controls", {}))
    if set(controls) != required_controls:
        errors.append("cross-cutting control set drift")

    required_component_bindings = {"audit", "quality", "learning", "ai_automation"}
    for component, data in matrix.get("components", {}).items():
        bindings = set(data.get("cross_cutting_controls", []))
        if bindings != required_component_bindings:
            errors.append(f"component {component} cross-cutting bindings drift")

    for stage in contract.get("canonical_flow", []):
        for key in ("stage", "owner", "output"):
            if not stage.get(key):
                errors.append(f"flow stage missing {key}")

    for rel in contract["required_cross_repo_anchors"]["foundation"]:
        require_text(foundation / rel, [], errors, f"foundation:{rel}")

    require_text(
        foundation / "tools/autonomous_mission_router.mjs",
        ["PROJECT_IMPROVEMENT_MATRIX", "scheduling_only"],
        errors,
        "foundation:router",
    )
    require_text(
        foundation / "tools/autonomous_engineering_supervisor.mjs",
        ["validatePlan", "PROJECT_IMPROVEMENT_MATRIX", "component_improvement"],
        errors,
        "foundation:supervisor",
    )

    if operations is not None:
        for rel in contract["required_cross_repo_anchors"]["operations"]:
            path = operations / rel
            if rel.endswith("/"):
                if not path.is_dir():
                    errors.append(f"operations:{rel}:missing")
            else:
                require_text(path, [], errors, f"operations:{rel}")

        require_text(
            operations / "private/evolution_engine.py",
            ["private.evolution_score", "next_learning_action"],
            errors,
            "operations:evolution-engine",
        )
        require_text(
            operations / "private/chatbot/chat_learning.py",
            ["LearningAuthority.CANDIDATE", "ChatLearningObservation"],
            errors,
            "operations:chat-learning",
        )
        require_text(
            operations / "private/chatbot/feedback_evaluation_bridge.py",
            ["EvaluationCaseCandidate", "LearningAuthority.CANDIDATE"],
            errors,
            "operations:feedback-bridge",
        )
        require_text(
            operations / "private/strategy_matrix.py",
            ["CandidateDisposition", "ELIGIBLE_FOR_SHADOW"],
            errors,
            "operations:strategy",
        )
        require_text(
            operations / "private/self_evolution_boundary.py",
            ["ProtectedAuthority", "CandidateStage.CANARY"],
            errors,
            "operations:self-evolution",
        )
        require_text(
            operations / "extractor_mapper/extraction/generic.py",
            ["def", "class"],
            errors,
            "operations:extractor",
        )
        workflows = operations / ".github" / "workflows"
        if workflows.is_dir() and any(path.is_file() for path in workflows.iterdir()):
            errors.append("operations:hosted workflow authority must remain absent")

    status = "PASS" if not errors else "FAIL"
    print(
        json.dumps(
            {
                "schema": "system-integration-receipt/v1",
                "status": status,
                "error_count": len(errors),
                "errors": errors,
            },
            indent=2,
        )
    )
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
