from pathlib import Path

from scripts.public_security_lint import active_files, lint_file

ROOT = Path(__file__).resolve().parents[1]

def test_active_files_includes_operational_public_types():
    files = {p.relative_to(ROOT).as_posix() for p in active_files(ROOT)}
    assert 'scripts/production_release.sh' in files
    assert any(p.endswith('.json') for p in files)
    assert any(p.startswith('docs/') and p.endswith('.md') for p in files)
    assert any(p.startswith('.github/workflows/') for p in files)

def test_private_references_are_exempt_only_on_intentional_nonruntime_surfaces(tmp_path):
    doc = tmp_path / 'example.md'
    doc.write_text('operations/private/control_plane_runtime.py\n', encoding='utf-8')
    assert not any(f.rule == 'private-reference' for f in lint_file(doc, tmp_path))
    workflow = tmp_path / 'workflow.yml'
    workflow.write_text('Z-Solo-King/operations@0123456789abcdef0123456789abcdef01234567\n', encoding='utf-8')
    assert not any(f.rule == 'private-revision' for f in lint_file(workflow, tmp_path))

def test_strict_findings_fail_without_special_flag():
    text = Path(ROOT / 'scripts/public_security_lint.py').read_text(encoding='utf-8')
    assert 'return 1 if findings else 0' in text

def test_generic_public_architecture_words_are_not_private_paths(tmp_path):
    doc = tmp_path / "architecture.md"
    doc.write_text("Operations handles resource ledger and promotion stages.\n", encoding="utf-8")
    assert not any(f.rule == "private-reference" for f in lint_file(doc, tmp_path))


def test_private_import_and_path_patterns_are_detected(tmp_path):
    samples = [
        "from private.chatbot.router import Router",
        "private/resource_ledger.py",
        "operations/private/control_plane_runtime.py",
    ]
    for index, sample in enumerate(samples):
        path = tmp_path / f"sample{index}.py"
        path.write_text(sample + "\n", encoding="utf-8")
        assert any(f.rule == "private-reference" for f in lint_file(path, tmp_path))


def test_private_boundary_findings_are_classified_by_surface():
    import scripts.public_security_lint as lint
    assert lint.private_reference_findings(Path("docs/example.md"), "private/foo.py") == []
    assert lint.private_reference_findings(Path(".github/workflows/example.yml"), "operations/private/foo.py") == []
    assert lint.private_reference_findings(Path("runtime.py"), "from private.foo import bar")
    assert lint.private_revision_findings(Path("docs/example.md"), "Z-Solo-King/operations@0123456789abcdef0123456789abcdef01234567") == []
    assert lint.private_revision_findings(Path("runtime.py"), "Z-Solo-King/operations@0123456789abcdef0123456789abcdef01234567")
