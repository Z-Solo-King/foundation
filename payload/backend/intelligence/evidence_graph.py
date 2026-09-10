from dataclasses import dataclass
from enum import StrEnum


class Relation(StrEnum):
    SUPPORTS = "supports"
    REFUTES = "refutes"
    QUALIFIES = "qualifies"
    CONTEXTUALIZES = "contextualizes"


@dataclass(frozen=True)
class EvidenceLink:
    claim_id: str
    evidence_id: str
    relation: Relation


@dataclass(frozen=True)
class EvidenceGraph:
    links: tuple[EvidenceLink, ...] = ()

    def add(self, link: EvidenceLink):
        return EvidenceGraph(self.links + (link,))

    def for_claim(self, claim_id: str):
        return tuple(x for x in self.links if x.claim_id == claim_id)
