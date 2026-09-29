from pathlib import Path

def test_deep_scan_workflow_is_unprivileged_and_frozen():
    text=(Path(__file__).resolve().parents[1]/'.github/workflows/open-issue-polyglot-deep-scan.yml').read_text(encoding='utf-8')
    assert 'pull_request_target:' not in text
    assert 'issues: write' not in text
    assert 'needs.snapshot.outputs.operations_sha' in text
    assert 'path: operations/.runtime/open-issue-deep-scan/*.json' in text
    assert 'retention-days: 7' in text
