"""Deterministic-first evidence verifier with semantic entailment and lineage checks."""

from dataclasses import dataclass
from datetime import datetime, timezone, timedelta

from backend.evaluation.entailment import EntailmentStatus, verify_claim_entailment
from backend.intelligence.observations import Observation, EvidenceSpan
from backend.intelligence.certificates import verify_certificate, EvidenceCertificate
from backend.intelligence.lineage import SourceLineage, is_independent
from backend.intelligence.contradiction import detect_contradiction
from backend.intelligence.claims import Claim


class ClaimStatus:
    SUPPORTED = "supported"
    CORROBORATED = "corroborated"
    CONTRADICTED = "contradicted"
    UNKNOWN = "unknown"
    INACCESSIBLE = "inaccessible"
    STALE = "stale"
    PARTIAL = "partial"
    INFERRED = "inferred"


@dataclass(frozen=True)
class VerificationResult:
    claim_id: str
    status: str
    supporting_evidence: tuple[EvidenceCertificate, ...] = ()
    contradicting_evidence: tuple[EvidenceCertificate, ...] = ()
    independent_corroboration_count: int = 0
    reasons: tuple[str, ...] = ()
    verified_at: datetime = None

    def __post_init__(self):
        if self.verified_at is None:
            object.__setattr__(self, "verified_at", datetime.now(timezone.utc))


class EvidenceVerifier:
    """Verifies evidence structurally and semantically before synthesis."""

    STALE_THRESHOLD = timedelta(days=30)

    def verify_span(self, certificate: EvidenceCertificate, observation: Observation) -> bool:
        return verify_certificate(observation, certificate)

    def check_contradiction(self, claim_a: Claim, claim_b: Claim) -> bool:
        return detect_contradiction(claim_a.text, claim_b.text) is not None

    def check_independence(self, lineage_a: SourceLineage, lineage_b: SourceLineage) -> bool:
        return is_independent(lineage_a, lineage_b)

    def is_stale(self, observation: Observation) -> bool:
        return datetime.now(timezone.utc) - observation.observed_at > self.STALE_THRESHOLD

    def verify_claim(self, claim: Claim, supporting_certs: tuple[EvidenceCertificate, ...], observations: dict[str, Observation], lineages: dict[str, SourceLineage], other_claims: tuple[Claim, ...] = ()) -> VerificationResult:
        reasons: list[str] = []
        supporting: list[EvidenceCertificate] = []
        contradicting: list[EvidenceCertificate] = []
        valid_lineages: list[SourceLineage] = []
        status = ClaimStatus.UNKNOWN

        if not supporting_certs:
            return VerificationResult(claim.claim_id, ClaimStatus.UNKNOWN, reasons=("no evidence provided",))

        for cert in supporting_certs:
            obs = observations.get(cert.observation_id)
            if not obs:
                reasons.append(f"observation {cert.observation_id} not found (inaccessible)")
                status = ClaimStatus.INACCESSIBLE
                continue
            if not self.verify_span(cert, obs):
                reasons.append(f"certificate span verification failed for {cert.observation_id}")
                contradicting.append(cert)
                status = ClaimStatus.CONTRADICTED
                continue

            span = EvidenceSpan(cert.observation_id, cert.span_start, cert.span_end)
            entailment = verify_claim_entailment(claim.text, obs, span)
            if entailment.status == EntailmentStatus.INVALID:
                reasons.append(f"semantic evidence span invalid for {cert.observation_id}")
                status = ClaimStatus.CONTRADICTED
                contradicting.append(cert)
                continue
            if entailment.status == EntailmentStatus.UNSUPPORTED:
                reasons.append(f"claim is not semantically supported by {cert.observation_id}: {entailment.reason}")
                status = ClaimStatus.PARTIAL if status != ClaimStatus.CONTRADICTED else status
                continue
            if entailment.status == EntailmentStatus.AMBIGUOUS:
                reasons.append(f"semantic entailment is ambiguous for {cert.observation_id}")
                status = ClaimStatus.PARTIAL if status != ClaimStatus.CONTRADICTED else status
                continue
            supporting.append(cert)
            lineage = lineages.get(cert.source_id)
            if lineage:
                valid_lineages.append(lineage)

        stale_count = sum(1 for cert in supporting if self.is_stale(observations[cert.observation_id]))
        all_supporting_stale = bool(supporting) and stale_count == len(supporting)
        if stale_count:
            reasons.append(f"{stale_count} supporting observations are stale (>30 days)")

        for other in other_claims:
            if other.claim_id == claim.claim_id:
                continue
            if self.check_contradiction(claim, other):
                reasons.append(f"claim contradicts {other.claim_id}")
                status = ClaimStatus.CONTRADICTED

        independent_lineages: list[SourceLineage] = []
        for lineage in valid_lineages:
            if not any(self.check_independence(lineage, existing) for existing in independent_lineages):
                independent_lineages.append(lineage)
        independent_count = len(independent_lineages)

        if independent_count == 0 and supporting:
            reasons.append("supporting evidence has no independently originating corroboration")
        elif independent_count >= 2:
            reasons.append(f"independent corroboration from {independent_count} origins")
        elif supporting:
            reasons.append("supporting evidence comes from one origin")

        if status == ClaimStatus.CONTRADICTED:
            final_status = ClaimStatus.CONTRADICTED
        elif not supporting:
            final_status = ClaimStatus.INACCESSIBLE if status == ClaimStatus.INACCESSIBLE else ClaimStatus.UNKNOWN
        elif all_supporting_stale:
            final_status = ClaimStatus.STALE
        elif stale_count or status in {ClaimStatus.INACCESSIBLE, ClaimStatus.PARTIAL}:
            final_status = ClaimStatus.PARTIAL
        elif independent_count >= 2:
            final_status = ClaimStatus.CORROBORATED
        else:
            final_status = ClaimStatus.SUPPORTED

        return VerificationResult(claim.claim_id, final_status, tuple(supporting), tuple(contradicting), independent_count, tuple(reasons))
