from pathlib import Path

ROOT = Path(__file__).parents[1]

def test_private_operations_has_no_github_actions_workflows():
    operations = ROOT / 'operations'
    if not operations.exists():
        return
    workflow_root = operations / '.github' / 'workflows'
    if not workflow_root.exists():
        return
    workflow_files = tuple(workflow_root.glob('*.yml')) + tuple(workflow_root.glob('*.yaml'))
    assert workflow_files == (), 'Private Operations must not own GitHub Actions workflows'

def test_foundation_is_the_documented_deployment_owner():
    text = (ROOT / 'tests' / 'test_workflow_policy.py').read_text(encoding='utf-8')
    assert 'PRODUCTION_WORKFLOW' in text
    assert 'production_release.sh' in text
