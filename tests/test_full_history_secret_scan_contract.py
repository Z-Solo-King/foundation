from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_full_history_secret_scan_stays_in_required_checks():
    workflow = (ROOT / ".github" / "workflows" / "required-pr-checks.yml").read_text(
        encoding="utf-8"
    )
    assert "Full tracked-tree and git-history secret scan" in workflow
    assert "public-full-secret-scan" in workflow
