from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_rule_lifecycle_contract_is_explicit():
    text = (ROOT / "docs" / "RULE_LIFECYCLE_CONTRACT.md").read_text(encoding="utf-8")
    for value in ("canonical owner", "enforcement point", "regression", "evidence tier", "runtime gate", "exception/retirement"):
        assert value in text
    assert "Duplicate authorities are prohibited" in text


def test_state_composition_does_not_promote_missing_execution_to_success():
    text = (ROOT / "docs" / "RULE_LIFECYCLE_CONTRACT.md").read_text(encoding="utf-8")
    assert "Missing execution is `UNKNOWN` or `NOT_ATTEMPTED`, never implicit success." in text
    assert "PARTIAL" in text
    assert "Structural validity, capability, readiness and resumability are separate dimensions." in text


def test_evidence_contract_is_family_canonical():
    text = (ROOT / "docs" / "EVIDENCE_VALIDATION_CONTRACT.md").read_text(encoding="utf-8")
    assert "Canonical family validation contract" in text
    assert "L1" in text and "L2" in text and "L3" in text and "L4" in text
