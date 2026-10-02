from __future__ import annotations

import json
import subprocess
from pathlib import Path

from tools.code_documentation_sync import matches, validate
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


def test_universal_text_rules_reject_crlf_trailing_whitespace_and_missing_newline(
    tmp_path: Path,
) -> None:
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


def _init_sync_fixture(tmp_path: Path, require_doc_update: bool, reason: str = "") -> Path:
    (tmp_path / "docs").mkdir()
    (tmp_path / "src.py").write_text("print('ok')\n", encoding="utf-8")
    (tmp_path / "docs" / "canonical.md").write_text("# Canonical\n", encoding="utf-8")
    (tmp_path / "docs" / "CODE_DOCUMENTATION_SYNC_MAP.json").write_text(
        json.dumps(
            {
                "schema_version": "code-doc-sync/v1",
                "repository": "fixture",
                "groups": [
                    {
                        "id": "fixture",
                        "code_paths": ["src.py"],
                        "docs": ["docs/canonical.md"],
                        "require_doc_update": require_doc_update,
                        **({"sync_exemption_reason": reason} if reason else {}),
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(["git", "add", "."], cwd=tmp_path, check=True)
    return tmp_path


def test_sync_exemption_requires_a_reason(tmp_path: Path) -> None:
    root = _init_sync_fixture(tmp_path, False)
    report = validate(root, changed_paths={"src.py"}, strict=True)
    assert any(item["rule"] == "sync-exemption-reason-required" for item in report["issues"])


def test_sync_exemption_with_reason_is_accepted(tmp_path: Path) -> None:
    root = _init_sync_fixture(tmp_path, False, "Generated adapter; source is intentionally independent.")
    report = validate(root, changed_paths={"src.py"}, strict=True)
    assert report["passed"] is True


def test_recursive_map_matching_and_current_map_integrity() -> None:
    assert matches("private/feed_recovery/builder.mjs", "private/feed_recovery/**")
    assert matches(".github/workflows/repository-hygiene.yml", ".github/workflows/*.yml")
    root = Path(__file__).parents[1]
    report = validate(root)
    assert report["passed"] is True
