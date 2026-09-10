from dataclasses import dataclass
from enum import StrEnum


class EvidenceRelation(StrEnum):
    SUPPORTS = "supports"
    REFUTES = "refutes"
    QUALIFIES = "qualifies"
    CONTEXTUALIZES = "contextualizes"


@dataclass(frozen=True)
class ClaimEvidence:
    claim_id: str
    evidence_id: str
    relation: EvidenceRelation
