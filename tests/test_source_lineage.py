from backend.source_lineage import (
    SourceFamily,
    SourceLineage,
    is_independent,
)


def test_same_family_is_not_independent():
    family = SourceFamily("family-001", "Example News")
    first = SourceLineage("source-001", family.family_id)
    second = SourceLineage("source-002", family.family_id)

    assert is_independent(first, second) is False


def test_different_families_can_be_independent():
    first_family = SourceFamily("family-001", "Example News")
    second_family = SourceFamily("family-002", "Independent Journal")

    first = SourceLineage("source-001", first_family.family_id)
    second = SourceLineage("source-002", second_family.family_id)

    assert is_independent(first, second) is True
