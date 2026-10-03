from pathlib import Path

WORKFLOW = Path(__file__).resolve().parents[1] / '.github' / 'workflows' / 'open-issue-polyglot-deep-scan.yml'

def test_deep_scan_uses_four_lanes_and_immutable_operations_snapshot():
    text = WORKFLOW.read_text(encoding='utf-8')
    assert 'lane: [L1, L2, L3, L4]' in text
    assert 'name: Deep scan ${{ matrix.lane }}' in text
    assert 'operations_sha: ${{ steps.freeze.outputs.sha }}' in text
    assert 'repository: Z-Solo-King/operations' in text
    assert 'ref: main' in text
    assert 'ref: ${{ needs.snapshot.outputs.operations_sha }}' in text
    assert 'git rev-parse HEAD' in text

def test_deep_scan_lane_provenance_records_both_repository_revisions():
    text = WORKFLOW.read_text(encoding='utf-8')
    assert 'operationsRevision' in text
    assert 'payload.foundation_revision' in text
    assert 'payload.operations_revision' in text
    assert 'FOUNDATION_REVISION: ${{ github.sha }}' in text

def test_deep_scan_uploads_sanitized_lane_receipts_even_on_failure():
    text = WORKFLOW.read_text(encoding='utf-8')
    assert 'Upload sanitized lane summary' in text
    assert 'if: always()' in text
    assert 'path: operations/.runtime/open-issue-deep-scan/*.json' in text

def test_deep_scan_aggregate_enforces_active_and_historical_lane_coverage():
    text = WORKFLOW.read_text(encoding='utf-8')
    assert 'open-issue-polyglot-deep-scan/v3' in text
    assert 'activePairsExpected' in text or 'active_pairs_expected' in text
    assert 'historicalIssues' in text or 'historical_issues' in text
    assert 'observedActive' in text or 'observed_active' in text
    assert 'observedHistorical' in text or 'observed_historical' in text

def test_deep_scan_aggregate_downloads_summary_artifacts_for_current_attempt():
    text = WORKFLOW.read_text(encoding='utf-8')
    assert 'open-issue-deep-scan-*-summary-${{ github.run_id }}-attempt-${{ github.run_attempt }}' in text
    assert 'open-issue-deep-scan-*-run-${{ github.run_id }}-attempt-${{ github.run_attempt }}' not in text
