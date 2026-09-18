"""Structured uncertainty and abstention projection for verified research claims.

This module classifies existing verifier states; it does not authorize publication or
replace the canonical evidence/publication authorities.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from backend.intelligence.verifier import ClaimStatus


SCHEMA = "claim-uncertainty/v1"


class AbstentionReason(StrEnum):
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"
    CONTRADICTION = "contradiction"
    STALE_EVIDENCE = "stale_evidence"
    INACCESSIBLE_EVIDENCE = "inaccessible_evidence"
    OUT_OF_SCOPE = "out_of_scope"


class UncertaintyState(StrEnum):
    SUPPORTED = "supported"
    QUALIFIED = "qualified"
    UNKNOWN = "unknown"
    CONTRADICTED = "contradicted"
    ABSTAIN = "abstain"


@dataclass(frozen=True)
class ClaimUncertainty:
    claim_id: str
    state: UncertaintyState
    evidence_sufficient: bool
    freshness_ok: bool
    independent_sources: int
    abstention_reason: AbstentionReason | None = None
    population_revision: str | None = None

    def validate(self) -> None:
        if not self.claim_id.strip():
            raise ValueError("claim_id is required")
        if self.independent_sources < 0:
            raise ValueError("independent_sources must be non-negative")
        if self.state is UncertaintyState.ABSTAIN and self.abstention_reason is None:
            raise ValueError("abstention requires a reason")
        if self.state is not UncertaintyState.ABSTAIN and self.abstention_reason is not None:
            raise ValueError("non-abstaining claims cannot carry an abstention reason")
        if self.population_revision is not None and not self.population_revision.strip():
            raise ValueError("population_revision must be non-empty when supplied")


def classify_claim_uncertainty(
    claim_id: str,
    verifier_status: str,
    *,
    evidence_sufficient: bool,
    freshness_ok: bool,
    independent_sources: int,
    population_revision: str | None = None,
) -> ClaimUncertainty:
    if verifier_status == ClaimStatus.CONTRADICTED:
        state, reason = UncertaintyState.CONTRADICTED, None
    elif verifier_status == ClaimStatus.STALE or not freshness_ok:
        state, reason = UncertaintyState.ABSTAIN, AbstentionReason.STALE_EVIDENCE
    elif verifier_status == ClaimStatus.INACCESSIBLE:
        state, reason = UncertaintyState.ABSTAIN, AbstentionReason.INACCESSIBLE_EVIDENCE
    elif verifier_status in {ClaimStatus.UNKNOWN} or not evidence_sufficient:
        state, reason = UncertaintyState.ABSTAIN, AbstentionReason.INSUFFICIENT_EVIDENCE
    elif verifier_status == ClaimStatus.PARTIAL:
        state, reason = UncertaintyState.QUALIFIED, None
    elif verifier_status in {ClaimStatus.CORROBORATED, ClaimStatus.SUPPORTED}:
        state, reason = UncertaintyState.SUPPORTED, None
    else:
        state, reason = UncertaintyState.ABSTAIN, AbstentionReason.OUT_OF_SCOPE
    result = ClaimUncertainty(
        claim_id,
        state,
        evidence_sufficient,
        freshness_ok,
        independent_sources,
        reason,
        population_revision,
    )
    result.validate()
    return result


def uncertainty_from_result(
    claim_id: str,
    verifier_status: str,
    *,
    evidence_count: int,
    freshness_ok: bool,
    independent_sources: int,
    population_revision: str | None = None,
) -> ClaimUncertainty:
    return classify_claim_uncertainty(
        claim_id,
        verifier_status,
        evidence_sufficient=evidence_count > 0,
        freshness_ok=freshness_ok,
        independent_sources=independent_sources,
        population_revision=population_revision,
    )
