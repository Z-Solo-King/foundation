from pathlib import Path
import yaml

ROOT=Path(__file__).resolve().parents[1]
WF=ROOT/".github/workflows/actions-static-analysis.yml"
FIXTURE=ROOT/"tests/fixtures/unsafe-pull-request-target.yml"

def test_security_workflow_is_sha_pinned_and_least_privileged():
    text=WF.read_text(encoding="utf-8")
    assert "zizmorcore/zizmor-action@cc914d7f3750a2d13d75c7f184a1060aa0e9d482" in text
    assert "min-severity: high" in text
    assert "ossf/scorecard-action@2d1146689b8cda280b9bc96326124645441f03bc" in text
    assert "security-events: write" not in text

def test_regression_fixture_is_explicitly_unsafe():
    data=yaml.safe_load(FIXTURE.read_text(encoding="utf-8"))
    triggers=data.get("on") or data.get(True)
    assert "pull_request_target" in triggers
    assert data["permissions"]["contents"]=="write"
