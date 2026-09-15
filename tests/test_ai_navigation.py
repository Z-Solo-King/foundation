import json
from pathlib import Path

from tools.validate_ai_navigation import validate_repository


def test_ai_navigation_metadata_matches_repository_tree():
    root = Path(__file__).resolve().parents[1]
    assert validate_repository(root) == []
    assert (root / "AI_NAVIGATION_INDEX.json").exists()
    assert not (root / "AI_CODEMAP.json").exists()


def test_ai_navigation_marks_external_documents_explicitly():
    root = Path(__file__).resolve().parents[1]
    index = json.loads((root / "AI_NAVIGATION_INDEX.json").read_text(encoding="utf-8"))
    assert all(
        value.startswith("Z-Solo-King/operations:") or value == "README.md" or value.startswith("docs/")
        for value in index["read_first"]
    )
