from __future__ import annotations

import json
from pathlib import Path

from tools.repository_hygiene import (
    build_report,
    check_bytes,
    is_forbidden_artifact,
    is_formatter_path,
    is_text_path,
)


def test_hygiene_contract_is_valid() -> None:
    root = Path(__file__).parents[1]
    contract = json.loads(
        (root / "docs" / "REPOSITORY_HYGIENE_FORMAT_CONTRACT.json").read_text(
            encoding="utf-8"
        )
    )
    assert contract["schema_version"] == "repository-hygiene-format/v1"
    assert contract["contract_version"] == "2026-10-02"


def test_universal_text_rules_reject_crlf_and_trailing_whitespace(tmp_path: Path) -> None:
    path = tmp_path / "sample.md"
    path.write_bytes(b"# Title\r\n\r\ntext  \r\n")
    rules = {item["rule"] for item in check_bytes(path, "sample.md")}
    assert {"lf-only", "trailing-whitespace"} <= rules


def test_text_and_formatter_scope_covers_code_and_documents() -> None:
    for path in ("app.py", "edge.ts", "config.json", "workflow.yml", "README.md", "deploy.sh"):
        assert is_text_path(path)
    for path in ("app.py", "edge.ts", "config.json", "workflow.yml", "README.md"):
        assert is_formatter_path(path)


def test_forbidden_artifact_detection_uses_glob_patterns() -> None:
    assert is_forbidden_artifact("backend/__pycache__/x.pyc")
    assert is_forbidden_artifact("coverage.xml")
    assert is_forbidden_artifact("worker.pyc")


def test_current_repo_hygiene_report_is_structurally_valid() -> None:
    root = Path(__file__).parents[1]
    report = build_report(
        root,
        [".editorconfig", "docs/REPOSITORY_HYGIENE_FORMAT_CONTRACT.json"],
        False,
    )
    assert report["files"]["files_checked"] == 2
