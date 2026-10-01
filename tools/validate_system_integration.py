#!/usr/bin/env python3
"""Fail-closed cross-repository cohesion validator."""
from __future__ import annotations

import argparse
import ast
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



def require_python_syntax(path: Path, errors: list[str], label: str) -> None:
    if not path.is_file():
        errors.append(f"{label}:missing")
        return
    try:
        ast.parse(path.read_text(encoding="utf-8", errors="strict"), filename=str(path))
    except (OSError, SyntaxError) as exc:
        errors.append(f"{label}:syntax:{exc}")


def validate_production_pin_consistency(foundation: Path, errors: list[str]) -> None:
    manifest_path = foundation / "docs/OPERATIONS_PIN_MANIFEST.json"
    approval_path = foundation / "docs/OPERATIONS_MAIN_APPROVAL.json"
    sync_path = foundation / "docs/FAMILY_SYNC_STATE.json"
    try:
        manifest = load(manifest_path)
        approval = load(approval_path)
        sync = load(sync_path)
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"production-pin:metadata:{exc}")
        return
    canonical = (((manifest.get("pins") or {}).get("production_runtime") or {}).get("sha"))
    if not isinstance(canonical, str) or len(canonical) != 40:
        errors.append("production-pin:manifest invalid")
        return
    if approval.get("approved_sha") != canonical:
        errors.append("production-pin:approval drift")
    observed = approval.get("production_observed_sha")
    pending = (
        observed != canonical
        and approval.get("observed_state") == "PENDING_PRODUCTION_CERTIFICATION"
        and (approval.get("promotion_evidence") or {}).get("production_certification_required_after_pin_change") is True
    )
    if observed != canonical and not pending:
        errors.append("production-pin:observed production revision is neither certified nor explicitly pending certification")
    if ((sync.get("runtime_pins") or {}).get("production_operations")) != canonical:
        errors.append("production-pin:family-sync drift")
    consumers = (
        ".github/workflows/nightly-research-provider-preflight.yml",
        ".github/workflows/live-chatbot-production-smoke.yml",
        ".github/workflows/live-nightly-research-canary.yml",
        ".github/workflows/nightly-multi-agent-research-v3.yml",
        "docs/CURRENT_SOURCE_OF_TRUTH.md",
        "docs/CONTINUE_MIGRATION_2026-10-01.md",
        "docs/INTERNAL_ACCESS_CAPABILITY_POLICY.md",
        "tests/operations_main_guard.test.mjs",
    )
    for rel in consumers:
        require_text(foundation / rel, [canonical], errors, "production-pin:" + rel)

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--foundation-root", type=Path, required=True)
    parser.add_argument("--operations-root", type=Path)
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()

    errors: list[str] = []
    foundation = args.foundation_root.resolve()
    validate_production_pin_consistency(foundation, errors)
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
        ["PROJECT_IMPROVEMENT_MATRIX"],
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

        for rel in (
            "private/evolution_score.py",
            "private/evolution_engine.py",
            "private/evolution_integration.py",
            "private/evaluation_receipt.py",
            "private/language_fit_policy.py",
            "private/migration_artifact_policy.py",
            "private/ai_maintainability_policy.py",
            "private/runtime_language_policy.py",
        ):
            require_python_syntax(operations / rel, errors, f"operations:{rel}")

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
