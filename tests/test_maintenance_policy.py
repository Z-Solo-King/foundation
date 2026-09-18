from pathlib import Path

from tools.validate_repository_governance import (
    ALLOWED_FOUNDATION_WORKFLOWS,
    FORBIDDEN_LEGACY_DOCS,
    validate_foundation,
    validate_operations,
)


ROOT = Path(__file__).resolve().parents[1]


def test_foundation_workflow_allowlist_is_explicit():
    assert "required-pr-checks.yml" in ALLOWED_FOUNDATION_WORKFLOWS
    assert "heroic-ai-production-release.yml" in ALLOWED_FOUNDATION_WORKFLOWS


def test_foundation_governance_contract_is_present():
    assert "docs/MAINTENANCE_CONTRACT.md" in {
        p.relative_to(ROOT).as_posix() for p in ROOT.rglob("docs/MAINTENANCE_CONTRACT.md")
    }
    assert not validate_foundation(ROOT)


def test_retired_guidance_filenames_are_explicitly_blocked():
    assert "CLAUDE_GUIDANCE.md" in FORBIDDEN_LEGACY_DOCS
    assert "AI_AGENT_HANDOFF.md" in FORBIDDEN_LEGACY_DOCS


def test_operations_policy_rejects_workflow_authority(tmp_path):
    (tmp_path / ".github" / "workflows").mkdir(parents=True)
    (tmp_path / ".github" / "workflows" / "bad.yml").write_text("name: bad\n", encoding="utf-8")
    for name in {
        "CURRENT_SOURCE_OF_TRUTH.md",
        "AGENT_MAINTENANCE_GUIDE.md",
        "FAMILY_OPERATING_MODEL.md",
        "GOVERNANCE_AND_EVIDENCE_STANDARD.md",
        "KNOWLEDGE_LIFECYCLE_STANDARD.md",
        "FUTURE_KNOWLEDGE_CATALOG.md",
        "CHATBOT_BOUNDARY.md",
    }:
        (tmp_path / "docs").mkdir(exist_ok=True)
        (tmp_path / "docs" / name).write_text("# canonical\n", encoding="utf-8")
    assert any("no .github/workflows" in error for error in validate_operations(tmp_path))
