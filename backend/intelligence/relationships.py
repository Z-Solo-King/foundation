from dataclasses import dataclass

from .evidence_graph import Relation

EvidenceRelation = Relation


@dataclass(frozen=True)
class ClaimEvidence:
    claim_id: str
    evidence_id: str
    relation: EvidenceRelation


__all__ = ["ClaimEvidence", "EvidenceRelation"]
