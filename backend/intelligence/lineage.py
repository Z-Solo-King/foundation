from dataclasses import dataclass


@dataclass(frozen=True)
class SourceFamily:
    family_id: str
    name: str


@dataclass(frozen=True)
class SourceLineage:
    source_id: str
    family_id: str
    parent_source_id: str | None = None
    lineage_type: str = "origin"


def is_independent(first: SourceLineage, second: SourceLineage) -> bool:
    return first.source_id != second.source_id and first.family_id != second.family_id
