from __future__ import annotations

from pathlib import Path

from tools.validate_family_full_coverage import classify, load_matrix


def test_matrix_has_unique_functional_surfaces() -> None:
    matrix = load_matrix()
    ids = [item["id"] for item in matrix["functional_surfaces"]]
    assert ids and len(ids) == len(set(ids))


def test_representative_primary_classification() -> None:
    matrix = load_matrix()
    assert classify("foundation", ".github/workflows/foo.yml", matrix) == "github_governance"
    assert classify("foundation", "foundation_core/product_mapping.py", matrix) == "deterministic_mapper_core"
    assert classify("operations", "private/chatbot/router.py", matrix) == "chatbot_control_plane"
    assert classify("operations", "extractor_mapper/contracts.py", matrix) == "extractor_mapper"


def test_unknown_path_is_not_silently_covered() -> None:
    matrix = load_matrix()
    assert classify("foundation", "not/a/real/root/file.xyz", matrix) is None
