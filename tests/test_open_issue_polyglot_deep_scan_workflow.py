from pathlib import Path

WORKFLOW = Path(__file__).resolve().parents[1] / ".github" / "workflows" / "open-issue-polyglot-deep-scan.yml"


def test_deep_scan_workflow_uses_real_matrix_expressions_and_expanded_provenance_paths():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert 'name: Deep scan ${{ matrix.lane }}' in text
    assert '--lane "${{ matrix.lane }}"' in text
    assert 'os.environ["GITHUB_WORKSPACE"]' in text
    assert 'payload["foundation_revision"] = os.environ["GITHUB_SHA"]' in text
    assert '["git", "-C", str(operations_root), "rev-parse", "HEAD"]' in text
    assert '["git", "-C", "$GITHUB_WORKSPACE", "rev-parse", "HEAD"]' not in text


def test_deep_scan_lane_receipts_upload_even_when_scan_fails():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert '      - name: Upload lane receipt\n        if: always()' in text
