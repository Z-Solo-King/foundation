from dataclasses import dataclass
import hashlib


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
    origin_fingerprint: str | None = None
    republisher_of: str | None = None

    def validate(self) -> None:
        if not self.source_id.strip() or not self.family_id.strip():
            raise ValueError("source_id and family_id must not be empty")
        if self.lineage_type not in {"origin", "republished", "derived"}:
            raise ValueError("invalid lineage_type")
        if not (self.origin_fingerprint or "").strip():
            raise ValueError("origin_fingerprint must not be empty")
        if self.lineage_type == "republished" and not (self.parent_source_id or self.republisher_of):
            raise ValueError("republished lineage must identify its origin")


def origin_fingerprint(origin: str) -> str:
    if not origin or not origin.strip():
        raise ValueError("origin must not be empty")
    return hashlib.sha256(origin.strip().lower().encode()).hexdigest()


def is_independent(first: SourceLineage, second: SourceLineage) -> bool:
    first.validate()
    second.validate()
    if first.source_id == second.source_id:
        return False
    if first.origin_fingerprint == second.origin_fingerprint:
        return False
    if first.source_id in {second.parent_source_id, second.republisher_of}:
        return False
    if second.source_id in {first.parent_source_id, first.republisher_of}:
        return False
    return True
