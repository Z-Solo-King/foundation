from pathlib import Path
import yaml

def test_standalone_full_history_secret_scan_is_independent():
    workflow = Path(".github/workflows/full-history-secret-scan.yml").read_text(encoding="utf-8")
    assert "Full history secret scan" in workflow
    assert "fetch-depth: 0" in workflow
    assert "tools/full_history_secret_scan.sh" in workflow
    required = Path(".github/workflows/required-pr-checks.yml").read_text(encoding="utf-8")
    assert "Full tracked-tree and git-history secret scan" not in required

def test_scan_script_has_fail_closed_schema():
    script=Path("tools/full_history_secret_scan.sh").read_text(encoding="utf-8")
    assert 'public-full-secret-scan/v1' in script
    assert 'status=FAIL' in script or 'status=PASS' in script
