from pathlib import Path

ROOT = Path(__file__).parents[1]


def test_security_analysis_workflow_is_pinned_and_least_privilege():
    text = (ROOT / ".github/workflows/ci-security-analysis.yml").read_text(encoding="utf-8")
    assert "zizmorcore/zizmor-action@cc914d7f3750a2d13d75c7f184a1060aa0e9d482" in text
    assert "ossf/scorecard-action@2d1146689b8cda280b9bc96326124645441f03bc" in text
    assert "github/codeql-action/upload-sarif@f205ea1c3313d32999d8d6a48b4f6530d4437b38" in text
    assert "permissions: {}" in text
    assert "contents: read" in text
    assert "persist-credentials: false" in text
    assert "pull_request" in text and "push" in text


def test_security_policy_defines_non_secret_severity_handling():
    text = (ROOT / "docs/CI_SECURITY_ANALYSIS_POLICY.md").read_text(encoding="utf-8")
    for marker in ("Critical/high", "Medium/low", "Tool/internal failures", "pinned to immutable commit SHAs"):
        assert marker in text
