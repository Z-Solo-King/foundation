import json
from pathlib import Path

from tools.validate_repository_map import validate_repository


def test_repository_map_matches_repository_tree():
    root = Path(__file__).resolve().parents[1]
    assert validate_repository(root) == []
    assert (root / "REPOSITORY_MAP.json").exists()
    assert not (root / "AI_CODEMAP.json").exists()


def test_repository_map_marks_external_documents_explicitly():
    root = Path(__file__).resolve().parents[1]
    mapping = json.loads((root / "REPOSITORY_MAP.json").read_text(encoding="utf-8"))
    assert all(
        value.startswith("Z-Solo-King/operations:") or value == "README.md" or value.startswith("docs/")
        for value in mapping["read_first"]
    )
