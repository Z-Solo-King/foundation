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


def test_deep_scan_lane_summary_uploads_even_when_scan_fails():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert '      - name: Upload sanitized lane summary\n        if: always()' in text


def test_deep_scan_freezes_operations_revision_once_and_reuses_exact_sha():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert 'outputs:\n      operations_sha: ${{ steps.freeze.outputs.sha }}' in text
    assert 'repository: Z-Solo-King/operations\n          ref: main\n' in text
    assert 'repository: Z-Solo-King/operations\n          ref: main\n' in text
    assert 'ref: ${{ needs.snapshot.outputs.operations_sha }}' in text
    assert 'needs: [snapshot, lane]' in text


def test_deep_scan_aggregate_uses_private_operations_access_and_exact_matrix_coverage():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert 'actions/create-github-app-token@' in text
    assert 'steps.operations-app-aggregate.outputs.token' in text
    assert 'open-issue-polyglot-deep-scan/v3' in text
    assert 'active_pairs_expected' in text
    assert 'historical_issues = {"foundation#1264", "foundation#1267", "foundation#1281", "operations#197"}' in text
    assert 'observed_active == expected_lane_pairs' in text
    assert 'observed_historical == {(issue, lane) for issue in historical_issues}' in text



def test_deep_scan_aggregate_download_pattern_matches_lane_summary_artifacts():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "open-issue-deep-scan-*-summary-${{ github.run_id }}-attempt-${{ github.run_attempt }}" in text
    assert "open-issue-deep-scan-*-run-${{ github.run_id }}-attempt-${{ github.run_attempt }}" not in text



def test_deep_scan_uploads_full_lane_receipts_for_aggregation():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "path: operations/.runtime/open-issue-deep-scan/*.json" in text
    assert 'receipts = [json.loads(path.read_text()) for path in sorted(root.glob("L?.json"))]' in text
    assert 'root.glob("L?-summary.json")' not in text
