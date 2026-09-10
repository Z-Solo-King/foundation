"""Evidence verifier with contradiction detection and independence checking.

Verification is deterministic first; all contradiction and independence checks
are performed before any AI involvement. Fail-closed on contradictions and
stale/inaccessible observations.
"""

from dataclasses import dataclass
from datetime import datetime, timezone, timedelta

from backend.intelligence.observations import Observation, EvidenceSpan
from backend.intelligence.certificates import verify_certificate, EvidenceCertificate
from backend.intelligence.lineage import SourceLineage, is_independent
from backend.intelligence.contradiction import detect_contradiction
from backend.intelligence.claims import Claim


class ClaimStatus:
    """Explicit claim epistemic states."""
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
    """Output of evidence verification."""
    claim_id: str
    status: str
    supporting_evidence: tuple[EvidenceCertificate, ...] = ()
    contradicting_evidence: tuple[EvidenceCertificate, ...] = ()
    independent_corroboration_count: int = 0
    reasons: tuple[str, ...] = ()
    verified_at: datetime = None
    
    def __post_init__(self):
        if self.verified_at is None:
            object.__setattr__(self, 'verified_at', datetime.now(timezone.utc))


class EvidenceVerifier:
    """Verifies evidence spans, detects contradictions, checks independence."""
    
    STALE_THRESHOLD = timedelta(days=30)
    
    def __init__(self):
        pass
    
    def verify_span(self, certificate: EvidenceCertificate, observation: Observation) -> bool:
        """Verify that a certificate accurately represents an observation span."""
        return verify_certificate(observation, certificate)
    
    def check_contradiction(self, claim_a: Claim, claim_b: Claim) -> bool:
        """Detect if two claims contradict each other."""
        return detect_contradiction(claim_a.text, claim_b.text) is not None
    
    def check_independence(
        self,
        lineage_a: SourceLineage,
        lineage_b: SourceLineage,
    ) -> bool:
        """Check if two sources are independent (different families)."""
        return is_independent(lineage_a, lineage_b)
    
    def is_stale(self, observation: Observation) -> bool:
        """Check if an observation is older than STALE_THRESHOLD."""
        age = datetime.now(timezone.utc) - observation.observed_at
        return age > self.STALE_THRESHOLD
    
    def verify_claim(
        self,
        claim: Claim,
        supporting_certs: tuple[EvidenceCertificate, ...],
        observations: dict[str, Observation],
        lineages: dict[str, SourceLineage],
    ) -> VerificationResult:
        """Comprehensive verification of a claim.
        
        Steps:
        1. Verify all certificate spans against observations
        2. Check for staleness
        3. Detect internal contradictions
        4. Count independent corroboration (different families)
        5. Return explicit status
        """
        reasons = []
        supporting = []
        contradicting = []
        independent_count = 0
        status = ClaimStatus.UNKNOWN
        
        if not supporting_certs:
            reasons.append("no evidence provided")
            status = ClaimStatus.UNKNOWN
            return VerificationResult(
                claim.claim_id,
                status,
                (),
                (),
                0,
                tuple(reasons),
            )
        
        # Step 1: Verify all certificate spans
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
            
            supporting.append(cert)
        
        # Step 2: Check for staleness
        stale_count = sum(1 for cert in supporting if self.is_stale(observations[cert.observation_id]))
        if stale_count > 0:
            reasons.append(f"{stale_count} supporting observations are stale (>30 days)")
            if stale_count == len(supporting):
                status = ClaimStatus.STALE
            elif status != ClaimStatus.CONTRADICTED:
                status = ClaimStatus.PARTIAL
        
        # Step 3: Count independent corroboration
        seen_families = set()
        for cert in supporting:
            lineage = lineages.get(cert.source_id)
            if lineage and lineage.family_id not in seen_families:
                seen_families.add(lineage.family_id)
                independent_count += 1
        
        if independent_count == 0 and supporting:
            reasons.append("supporting evidence comes from single source family")
            if status not in (ClaimStatus.CONTRADICTED, ClaimStatus.STALE):
                status = ClaimStatus.SUPPORTED
        elif independent_count >= 2:
            reasons.append(f"independent corroboration from {independent_count} families")
            status = ClaimStatus.CORROBORATED
        elif supporting and status not in (ClaimStatus.CONTRADICTED, ClaimStatus.STALE):
            status = ClaimStatus.SUPPORTED
        
        return VerificationResult(
            claim.claim_id,
            status,
            tuple(supporting),
            tuple(contradicting),
            independent_count,
            tuple(reasons),
        )
