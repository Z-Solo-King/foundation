"""Deterministic structural policy checks for the Heroic AI repository family."""

from __future__ import annotations

from pathlib import Path

FOUNDATION = "foundation"
OPERATIONS = "operations"

FORBIDDEN_LEGACY_DOCS = {
    "AI_AGENT_HANDOFF.md",
    "AI_ANALYSIS_MAP.md",
    "CLAUDE_GUIDANCE.md",
    "CODE_OWNERSHIP_AND_PLACEMENT.md",
    "AI_AUDIT_AND_VERIFICATION_STANDARD.md",
    "AI_GOVERNANCE_STANDARD.md",
    "FAMILY_ARCHITECTURE.md",
    "FAMILY_DOCUMENTATION_INDEX.md",
    "GOVERNANCE_KNOWLEDGE_TAXONOMY.md",
    "LIMITATION_KNOWLEDGE_STANDARD.md",
}

CANONICAL_OPERATION_DOCS = {
    "CURRENT_SOURCE_OF_TRUTH.md",
    "AGENT_MAINTENANCE_GUIDE.md",
    "FAMILY_OPERATING_MODEL.md",
    "GOVERNANCE_AND_EVIDENCE_STANDARD.md",
    "KNOWLEDGE_LIFECYCLE_STANDARD.md",
    "FUTURE_KNOWLEDGE_CATALOG.md",
    "CHATBOT_BOUNDARY.md",
}

PRIVATE_WORKFLOW_FORBIDDEN_MARKERS = (
    "autonomous-benchmark",
    "autonomous-scorecard",
    "nightly-multi-agent-research",
    "nightly-research-contract",
    "operations-centralized-validation",
    "foundation-canonical-workflow-bridge",
    "canonical-nightly-pin-repair",
    "release-quality-regression",
)


def _files(root: Path) -> set[str]:
    return {
        p.relative_to(root).as_posix()
        for p in root.rglob("*")
        if p.is_file()
        and ".git" not in p.parts
        and not any(part in {"__pycache__", ".pytest_cache", "node_modules"} for part in p.parts)
    }


def validate_foundation(root: Path) -> list[str]:
    paths = _files(root)
    errors: list[str] = []

    if "benchmark" in {p.split("/", 1)[0] for p in paths}:
        errors.append("Foundation must not contain an active top-level benchmark/ directory")

    workflows = [p for p in paths if p.startswith(".github/workflows/")]
    for path in workflows:
        lowered = path.lower()
        if any(marker in lowered for marker in PRIVATE_WORKFLOW_FORBIDDEN_MARKERS):
            errors.append(f"Foundation contains retired/private workflow class: {path}")

    for path in paths:
        if path.startswith("docs/") and Path(path).name in FORBIDDEN_LEGACY_DOCS:
            errors.append(f"Foundation contains retired duplicate guidance document: {path}")
        if "/archives/" in path and path.startswith("private/") is False:
            errors.append(f"Archive material must stay under Operations private/archives/: {path}")

    if "docs/MAINTENANCE_CONTRACT.md" not in paths:
        errors.append("Missing canonical docs/MAINTENANCE_CONTRACT.md")
    if "REPOSITORY_MAP.json" not in paths:
        errors.append("Missing REPOSITORY_MAP.json")

    return errors


def validate_operations(root: Path) -> list[str]:
    paths = _files(root)
    errors: list[str] = []

    workflow_paths = [p for p in paths if p.startswith(".github/workflows/")]
    if workflow_paths:
        errors.append("Operations must contain no .github/workflows/ files")

    active_benchmark = [p for p in paths if p.startswith("benchmark/")]
    if active_benchmark:
        errors.append("Operations must not recreate a top-level benchmark/ authority; use private benchmark/runtime owners")

    for path in paths:
        if path.startswith("docs/") and Path(path).name in FORBIDDEN_LEGACY_DOCS:
            errors.append(f"Operations contains retired duplicate guidance document: {path}")

    for name in CANONICAL_OPERATION_DOCS:
        path = f"docs/{name}"
        if path not in paths:
            errors.append(f"Missing canonical Operations document: {path}")

    archive_paths = [p for p in paths if p.startswith("private/archives/")]
    for path in archive_paths:
        if path.endswith(".py") and ("private/archives/" not in path):
            errors.append(f"Archived Python must stay beneath private/archives/: {path}")

    return errors


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--foundation", type=Path, default=Path("."))
    parser.add_argument("--operations", type=Path)
    args = parser.parse_args()

    errors = validate_foundation(args.foundation.resolve())
    if args.operations:
        errors.extend(validate_operations(args.operations.resolve()))

    if errors:
        print("\n".join(errors))
        return 1

    print("repository maintenance governance: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
