from datetime import datetime

import pytest


def test_contradiction_scope_and_quantity_remaining_branches():
    from backend.intelligence.contradiction import TypedClaim, _scopes_overlap, detect_typed_contradiction

    assert _scopes_overlap(None, "x") is True
    assert _scopes_overlap("A", "a") is True
    assert _scopes_overlap("A", "B") is False

    def claim(cid, value, value_type, **changes):
        data = dict(
            entity="E", predicate="P", scope=None,
            valid_from=None, valid_until=None, unit="u",
            qualifier="q", version=None,
        )
        data.update(changes)
        return TypedClaim(cid, data.pop("entity"), data.pop("predicate"), value, value_type, **data)

    assert detect_typed_contradiction(
        claim("a", 1, "numeric", valid_from=datetime(2024, 1, 2)),
        claim("b", 2, "numeric", valid_until=datetime(2024, 1, 1)),
    ) is None
    assert detect_typed_contradiction(claim("a", 1, "quantity"), claim("b", 2, "quantity")) is not None
    assert detect_typed_contradiction(claim("a", "x", "text", qualifier="A"), claim("b", "x", "text", qualifier="B")) is not None
    assert detect_typed_contradiction(claim("a", "x", "text"), claim("b", "x", "text")) is None


def test_lineage_constructor_and_validation_branch_matrix():
    from backend.intelligence.lineage import SourceLineage

    with pytest.raises(ValueError, match="origin_fingerprint"):
        SourceLineage("s", "f", lineage_type="republished")
    with pytest.raises(ValueError, match="identify its origin"):
        SourceLineage("s", "f", lineage_type="republished", origin_fingerprint="fp")
    with pytest.raises(ValueError, match="invalid lineage_type"):
        SourceLineage("s", "f", lineage_type="invalid").validate()
    with pytest.raises(ValueError):
        SourceLineage("", "f").validate()


def test_source_constructor_string_type_path_is_validated():
    from backend.intelligence.sources import Source

    source = Source("s", "https://example.com", "web", family_id="f")
    assert source.validate() is None
    assert source.lineage("fp").origin_fingerprint == "fp"
