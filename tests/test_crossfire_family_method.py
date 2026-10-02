from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_crossfire_family_method_is_non_authoritative() -> None:
    text = (ROOT / "docs" / "CROSS_FIRE_FAMILY_METHOD.md").read_text(encoding="utf-8")
    assert "not as a private policy or promotion authority" in text
    assert "Up to six disjoint lanes" in text
    assert "model agreement never becomes policy, acceptance, merge, or deployment authority" in text


def test_crossfire_family_method_preserves_single_owner_rule() -> None:
    text = (ROOT / "docs" / "CROSS_FIRE_FAMILY_METHOD.md").read_text(encoding="utf-8")
    assert "Do not create a second scheduler, provider router, ledger, policy engine, or evidence authority." in text
