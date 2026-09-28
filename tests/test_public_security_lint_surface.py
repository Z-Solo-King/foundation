from pathlib import Path

from scripts.public_security_lint import active_files, lint_file, private_reference_findings


ROOT = Path(__file__).resolve().parents[1]


def test_active_files_includes_operational_public_types():
    files = {p.relative_to(ROOT).as_posix() for p in active_files(ROOT)}
    assert "scripts/production_release.sh" in files
    assert any(p.endswith(".json") for p in files)
    assert any(p.startswith("docs/") and p.endswith(".md") for p in files)
    assert any(p.startswith(".github/workflows/") for p in files)


def test_docs_and_tests_can_describe_private_boundaries_without_false_positive():
    assert private_reference_findings(Path("docs/example.md"), "operations/private/runtime_policy.py") == []
    assert private_reference_findings(Path("tests/example.py"), "from private.chatbot.router import Router") == []


def test_runtime_private_imports_and_paths_are_detected(tmp_path):
    for index, sample in enumerate([
        "from private.chatbot.router import Router",
        "operations/private/control_plane_runtime.py",
    ]):
        path = tmp_path / f"sample{index}.py"
        path.write_text(sample + "\n", encoding="utf-8")
        findings = lint_file(path, tmp_path)
        assert any(f.rule == "private-reference" for f in findings)


def test_workflow_direct_private_execution_is_detected(tmp_path):
    path = tmp_path / ".github" / "workflows" / "bad.yml"
    path.parent.mkdir(parents=True)
    path.write_text("python operations/private/multi_agent/migration_review.py\n", encoding="utf-8")
    findings = lint_file(path, tmp_path)
    assert any(f.rule == "workflow-private-execution" for f in findings)


def test_private_revision_is_detected_in_runtime_source(tmp_path):
    path = tmp_path / "runtime.py"
    path.write_text("OPS_SHA = 'Z-Solo-King/operations@0123456789abcdef0123456789abcdef01234567'\n", encoding="utf-8")
    findings = lint_file(path, tmp_path)
    assert any(f.rule == "private-revision" for f in findings)


def test_strict_fail_closed_is_not_optional():
    text = (ROOT / "scripts" / "public_security_lint.py").read_text(encoding="utf-8")
    assert "return 1 if findings else 0" in text
