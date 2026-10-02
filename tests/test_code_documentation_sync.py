from __future__ import annotations

import json
import subprocess
from pathlib import Path

from tools.code_documentation_sync import matches, validate


def test_contract_map_is_valid() -> None:
    root = Path(__file__).parents[1]
    data = json.loads(
        (root / "docs" / "CODE_DOCUMENTATION_SYNC_MAP.json").read_text(
            encoding="utf-8"
        )
    )
    assert data["schema_version"] == "code-doc-sync/v1"
    assert data["groups"]


def test_recursive_map_matching_and_current_map_integrity() -> None:
    assert matches("private/feed_recovery/builder.mjs", "private/feed_recovery/**")
    assert matches(".github/workflows/repository-hygiene.yml", ".github/workflows/*.yml")
    root = Path(__file__).parents[1]
    report = validate(root)
    assert report["passed"] is True


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
    assert any(
        item["rule"] == "sync-exemption-reason-required" for item in report["issues"]
    )


def test_sync_exemption_with_reason_is_accepted(tmp_path: Path) -> None:
    root = _init_sync_fixture(
        tmp_path,
        False,
        "Generated adapter; source is intentionally independent.",
    )
    report = validate(root, changed_paths={"src.py"}, strict=True)
    assert report["passed"] is True
