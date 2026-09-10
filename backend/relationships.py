from enum import StrEnum


class EvidenceRelation(StrEnum):
    SUPPORTS = "supports"
    REFUTES = "refutes"
    QUALIFIES = "qualifies"
    CONTEXTUALIZES = "contextualizes"
