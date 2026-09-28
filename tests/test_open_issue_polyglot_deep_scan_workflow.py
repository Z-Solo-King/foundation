from pathlib import Path

WORKFLOW = Path(__file__).resolve().parents[1] / ".github" / "workflows" / "open-issue-polyglot-deep-scan.yml"

def test_deep_scan_workflow_uses_real_matrix_expressions_and_provenance():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert 'name: Deep scan \${{ matrix.lane }}' in text
    assert '--lane "\${{ matrix.lane }}"' in text
    assert 'os.environ["GITHUB_WORKSPACE"]' in text
    assert 'payload["foundation_revision"] = os.environ["GITHUB_SHA"]' in text
    assert '["git", "-C", str(operations_root), "rev-parse", "HEAD"]' in text
    assert '["git", "-C", "$GITHUB_WORKSPACE", "rev-parse", "HEAD"]' not in text

def test_deep_scan_lane_receipts_upload_even_when_scan_fails():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert '      - name: Upload lane receipt\n        if: always()' in text

def test_deep_scan_freezes_operations_revision_once_and_reuses_exact_sha():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert 'outputs:\n      operations_sha: \${{ steps.freeze.outputs.sha }}' in text
    assert 'repository: Z-Solo-King/operations\n          ref: main\n' in text
    assert 'repository: Z-Solo-King/operations\n          ref: \${{ needs.snapshot.outputs.operations_sha }}\n' in text
    assert 'needs: [snapshot, lane]' in text

def test_deep_scan_snapshot_does_not_self_reference_job_output():
    text = WORKFLOW.read_text(encoding="utf-8")
    snapshot = text.split('  snapshot:', 1)[1].split('  lane:', 1)[0]
    assert 'needs.snapshot.outputs.operations_sha' not in snapshot

def test_deep_scan_aggregate_uses_private_operations_access():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert 'actions/create-github-app-token@' in text
    assert 'steps.operations-app-aggregate.outputs.token' in text
    assert 'open-issue-deep-scan/v3' in text
