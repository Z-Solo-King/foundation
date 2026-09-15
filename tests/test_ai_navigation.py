from pathlib import Path

from tools.validate_ai_navigation import validate_repository


def test_ai_navigation_metadata_matches_repository_tree():
    root = Path(__file__).resolve().parents[1]
    assert validate_repository(root) == []
