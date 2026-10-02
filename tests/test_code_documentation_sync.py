from __future__ import annotations

import json
from pathlib import Path

from tools.code_documentation_sync import matches, validate


def test_contract_map_is_valid() -> None:
    root = Path(__file__).parents[1]
    data = json.loads((root / "docs" / "CODE_DOCUMENTATION_SYNC_MAP.json").read_text(encoding="utf-8"))
    assert data["schema_version"] == "code-doc-sync/v1"
    assert data["groups"]


def test_glob_matching_handles_recursive_directory_patterns() -> None:
    assert matches("private/feed_recovery/builder.mjs", "private/feed_recovery/**")
    assert matches(".github/workflows/repository-hygiene.yml", ".github/workflows/*.yml")


def test_current_map_has_no_structural_errors() -> None:
    root = Path(__file__).parents[1]
    report = validate(root)
    assert report["passed"] is True
