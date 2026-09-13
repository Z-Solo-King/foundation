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

    def __init__(self, *, semantic_strict: bool = False):
        self.semantic_strict = semantic_strict

    def verify_span(self, certificate: EvidenceCertificate, observation: Observation) -> bool:
        return verify_certificate(observation, certificate)

    def check_contradiction(self, claim_a: Claim, claim_b: Claim) -> bool:
        return detect_contradiction(claim_a.text, claim_b.text) is not None

    def check_independence(self, lineage_a: SourceLineage, lineage_b: SourceLineage) -> bool:
        return is_independent(lineage_a, lineage_b)

    def is_stale(self, observation: Observation) -> bool:
        return datetime.now(timezone.utc) - observation.observed_at > self.STALE_THRESHOLD

    def verify_claim(self, claim, supporting_certs, observations, lineages, other_claims=()):
        if not supporting_certs:
            return VerificationResult(claim.claim_id, ClaimStatus.UNKNOWN, reasons=("no evidence provided",))
        inspected = self._inspect_evidence(claim, supporting_certs, observations, lineages)
        supporting, contradicting, reasons, semantic_reasons, valid_lineages, status = inspected
        stale_count = self._stale_count(supporting, observations, reasons)
        status = self._apply_claim_contradictions(claim, other_claims, status, reasons)
        independent_count = self._independent_count(valid_lineages, reasons)
        reasons.extend(semantic_reasons)
        final_status = self._final_status(status, supporting, stale_count, independent_count)
        return VerificationResult(claim.claim_id, final_status, tuple(supporting), tuple(contradicting), independent_count, tuple(reasons))

    def _inspect_evidence(self, claim, certificates, observations, lineages):
        reasons, semantic_reasons, supporting, contradicting, valid_lineages = [], [], [], [], []
        status = ClaimStatus.UNKNOWN
        for cert in certificates:
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
            if entailment.status in {EntailmentStatus.UNSUPPORTED, EntailmentStatus.AMBIGUOUS}:
                semantic_reasons.append(f"semantic entailment for {cert.observation_id}: {entailment.reason}")
                if self.semantic_strict:
                    status = ClaimStatus.PARTIAL if status != ClaimStatus.CONTRADICTED else status
                    continue
            supporting.append(cert)
            lineage = lineages.get(cert.source_id)
            if lineage:
                valid_lineages.append(lineage)
        return supporting, contradicting, reasons, semantic_reasons, valid_lineages, status

    def _stale_count(self, supporting, observations, reasons):
        stale_count = sum(1 for cert in supporting if self.is_stale(observations[cert.observation_id]))
        if stale_count:
            reasons.append(f"{stale_count} supporting observations are stale (>30 days)")
        return stale_count

    def _apply_claim_contradictions(self, claim, other_claims, status, reasons):
        for other in other_claims:
            if other.claim_id != claim.claim_id and self.check_contradiction(claim, other):
                reasons.append(f"claim contradicts {other.claim_id}")
                status = ClaimStatus.CONTRADICTED
        return status

    def _independent_count(self, valid_lineages, reasons):
        by_source = {lineage.source_id: lineage for lineage in valid_lineages}
        independent: list[SourceLineage] = []
        for lineage in sorted(by_source.values(), key=lambda item: item.source_id):
            if not independent or all(self.check_independence(lineage, existing) for existing in independent):
                independent.append(lineage)
        count = len(independent)
        if count == 0 and valid_lineages:
            reasons.append("supporting evidence has no independently originating corroboration")
        elif count >= 2:
            reasons.append(f"independent corroboration from {count} sources")
        elif valid_lineages:
            reasons.append("supporting evidence comes from one source")
        return count

    @staticmethod
    def _final_status(status, supporting, stale_count, independent_count):
        all_supporting_stale = bool(supporting) and stale_count == len(supporting)
        if status == ClaimStatus.CONTRADICTED:
            return ClaimStatus.CONTRADICTED
        if not supporting:
            return ClaimStatus.INACCESSIBLE if status == ClaimStatus.INACCESSIBLE else ClaimStatus.UNKNOWN
        if all_supporting_stale:
            return ClaimStatus.STALE
        if stale_count or status in {ClaimStatus.INACCESSIBLE, ClaimStatus.PARTIAL}:
            return ClaimStatus.PARTIAL
        if independent_count >= 2:
            return ClaimStatus.CORROBORATED
        return ClaimStatus.SUPPORTED
