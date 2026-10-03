from __future__ import annotations

import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).parents[1]
SYNC_TOOL = ROOT / "tools" / "code_documentation_sync.mjs"


def test_contract_map_is_valid() -> None:
    data = json.loads(
        (ROOT / "docs" / "CODE_DOCUMENTATION_SYNC_MAP.json").read_text(
            encoding="utf-8"
        )
    )
    assert data["schema_version"] == "code-doc-sync/v1"
    assert data["groups"]
    assert SYNC_TOOL.is_file()


def test_current_map_integrity_uses_canonical_node_tool() -> None:
    result = subprocess.run(
        ["node", str(SYNC_TOOL), "--root", str(ROOT), "--all", "--strict"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_sync_tool_uses_recursive_glob_matching() -> None:
    text = SYNC_TOOL.read_text(encoding="utf-8")
    assert "endsWith(\"/**\")" in text
    assert "matches(p, pattern)" in text
    assert "sync-exemption-reason-required" in text
