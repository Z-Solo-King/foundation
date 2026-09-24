from pathlib import Path

from scripts.public_security_lint import lint_file


def test_public_lint_allows_memory_only_session_token():
    path = Path("frontend/chat_view.js")
    assert not [f for f in lint_file(path) if f.rule in {"private-marker", "credential-literal"}]


def test_public_lint_detects_private_marker(tmp_path: Path):
    path = tmp_path / "example.js"
    path.write_text("const x = 'operations';\n", encoding="utf-8")
    assert any(f.rule == "private-marker" for f in lint_file(path, tmp_path))


def test_public_lint_detects_unsafe_extractall(tmp_path: Path):
    path = tmp_path / "archive_reader.py"
    path.write_text('"""reader"""\nimport zipfile\n\narchive = zipfile.ZipFile("x.zip")\narchive.extractall("out")\n', encoding="utf-8")
    assert any(f.rule == "unsafe-archive-extraction" for f in lint_file(path, tmp_path))


def test_public_lint_detects_network_import_in_planner(tmp_path: Path):
    path = tmp_path / "planner.py"
    path.write_text('"""planner"""\nimport requests\n\ndef plan():\n    return requests.get("https://example.test")\n', encoding="utf-8")
    assert any(f.rule == "planner-network" for f in lint_file(path, tmp_path))