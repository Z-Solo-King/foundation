from __future__ import annotations

import subprocess
from pathlib import Path


ROOT = Path(__file__).parents[1]
HYGIENE_TOOL = ROOT / "tools" / "repository_hygiene.mjs"


def test_current_repo_hygiene_report_is_clean() -> None:
    result = subprocess.run(
        ["node", str(HYGIENE_TOOL), "--root", str(ROOT), "--all", "--strict"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_hygiene_tool_defines_core_byte_rules() -> None:
    text = HYGIENE_TOOL.read_text(encoding="utf-8")
    for marker in (
        "lf-only",
        "final-newline",
        "trailing-whitespace",
        "tracked-artifact",
    ):
        assert marker in text


def test_hygiene_tool_formats_supported_project_files() -> None:
    text = HYGIENE_TOOL.read_text(encoding="utf-8")
    assert '".json"' in text
    assert '".yml"' in text
    assert '".mjs"' in text
