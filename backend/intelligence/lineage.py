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

    def __post_init__(self):
        self.validate()

    def validate(self) -> None:
        if not self.source_id.strip() or not self.family_id.strip():
            raise ValueError("source_id and family_id must not be empty")
        if self.lineage_type not in {"origin", "republished", "derived"}:
            raise ValueError("invalid lineage_type")
        if self.lineage_type == "republished":
            if not (self.origin_fingerprint or "").strip():
                raise ValueError("republished lineage requires origin_fingerprint")
            if not (self.parent_source_id or self.republisher_of):
                raise ValueError("republished lineage must identify its origin")

    @property
    def effective_origin(self) -> str:
        value = (self.origin_fingerprint or "").strip()
        return value if value else f"family:{self.family_id.strip().lower()}"


def origin_fingerprint(origin: str) -> str:
    if not origin or not origin.strip():
        raise ValueError("origin must not be empty")
    return hashlib.sha256(origin.strip().lower().encode()).hexdigest()


def is_independent(first: SourceLineage, second: SourceLineage) -> bool:
    if first.source_id == second.source_id:
        return False
    first.validate()
    second.validate()
    if first.effective_origin == second.effective_origin:
        return False
    if first.parent_source_id == second.source_id or second.parent_source_id == first.source_id:
        return False
    if first.republisher_of == second.source_id or second.republisher_of == first.source_id:
        return False
    return True
