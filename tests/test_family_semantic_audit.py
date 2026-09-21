from pathlib import Path

ROOT = Path(__file__).parents[1]
FORBIDDEN = ('wrangler deploy', 'cloudflare/wrangler-action', 'cloudflare workers deploy')

def test_operations_source_has_no_competing_deploy_invocation():
    operations = ROOT / 'operations'
    if not operations.exists():
        return
    excluded = {'security_trust_lint.py'}
    suffixes = {'.py', '.sh', '.toml', '.yml', '.yaml'}
    violations = []
    for path in operations.rglob('*'):
        if not path.is_file() or path.name in excluded or path.suffix.lower() not in suffixes:
            continue
        if 'tests' in path.parts:
            continue
        text = path.read_text(encoding='utf-8', errors='ignore')
        for marker in FORBIDDEN:
            if marker in text:
                violations.append(f'{path}:{marker}')
    assert violations == []

def test_operations_workflow_authority_boundary_is_explicit():
    operations = ROOT / 'operations'
    if not operations.exists():
        return
    agents = (operations / 'AGENTS.md').read_text(encoding='utf-8')
    assert 'GitHub Actions remains the canonical CI/CD/deployment authority for Foundation' in agents
    assert 'Do not add or re-enable competing Cloudflare Workers Builds/Deploy Hooks' in agents
