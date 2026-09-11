import pytest

from backend.source_lineage import SourceFamily, SourceLineage, is_independent


def lineage(source_id, family_id, origin, **kwargs):
    return SourceLineage(source_id, family_id, origin_fingerprint=origin, **kwargs)


def test_same_origin_is_not_independent_even_with_different_families():
    family = SourceFamily("family-001", "Example News")
    first = lineage("source-001", family.family_id, "origin-a")
    second = lineage("source-002", "family-002", "origin-a")

    assert is_independent(first, second) is False


def test_different_origins_can_be_independent():
    first_family = SourceFamily("family-001", "Example News")
    second_family = SourceFamily("family-002", "Independent Journal")

    first = lineage("source-001", first_family.family_id, "origin-a")
    second = lineage("source-002", second_family.family_id, "origin-b")

    assert is_independent(first, second) is True


def test_republisher_is_not_independent_of_parent():
    first = lineage("source-001", "family-001", "origin-a")
    second = lineage("source-002", "family-002", "origin-b", parent_source_id="source-001", lineage_type="republished")
    assert is_independent(first, second) is False


def test_republished_lineage_requires_origin_link():
    with pytest.raises(ValueError):
        lineage("source-002", "family-002", "origin-b", lineage_type="republished")
