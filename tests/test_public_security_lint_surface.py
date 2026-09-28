from pathlib import Path

from scripts.public_security_lint import active_files, lint_file

ROOT = Path(__file__).resolve().parents[1]

def test_active_files_includes_operational_public_types():
    files = {p.relative_to(ROOT).as_posix() for p in active_files(ROOT)}
    assert 'scripts/production_release.sh' in files
    assert any(p.endswith('.json') for p in files)
    assert any(p.startswith('docs/') and p.endswith('.md') for p in files)
    assert any(p.startswith('.github/workflows/') for p in files)

def test_private_references_are_not_exempt_in_docs_or_workflows(tmp_path):
    doc = tmp_path / 'example.md'
    doc.write_text('operations/private/control_plane_runtime.py\n', encoding='utf-8')
    assert any(f.rule == 'private-reference' for f in lint_file(doc, tmp_path))
    workflow = tmp_path / 'workflow.yml'
    workflow.write_text('Z-Solo-King/operations@0123456789abcdef0123456789abcdef01234567\n', encoding='utf-8')
    assert any(f.rule == 'private-reference' for f in lint_file(workflow, tmp_path))

def test_strict_findings_fail_without_special_flag():
    text = Path(ROOT / 'scripts/public_security_lint.py').read_text(encoding='utf-8')
    assert 'return 1 if findings else 0' in text