from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_rule_lifecycle_contract_is_explicit():
    text = (ROOT / "docs" / "AI_AUDIT_AND_VERIFICATION_STANDARD.md").read_text(encoding="utf-8")
    for value in ("canonical owner", "enforcement point", "regression", "evidence tier", "runtime gate", "retirement"):
        assert value in text
    assert "Duplicate authorities" in text


def test_state_composition_does_not_promote_missing_execution_to_success():
    text = (ROOT / "docs" / "AI_AUDIT_AND_VERIFICATION_STANDARD.md").read_text(encoding="utf-8")
    assert "Missing execution" in text
    assert "PARTIAL" in text
    assert "evidence" in text.lower()


def test_evidence_contract_is_family_canonical():
    text = (ROOT / "docs" / "AI_AUDIT_AND_VERIFICATION_STANDARD.md").read_text(encoding="utf-8")
    assert all(value in text for value in ("L0", "L1", "L2", "L3", "L4"))
