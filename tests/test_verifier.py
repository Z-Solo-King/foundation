"""Tests for evidence verification."""

from datetime import datetime, timezone, timedelta
from backend.intelligence.verifier import EvidenceVerifier, ClaimStatus
from backend.intelligence.certificates import create_certificate
from backend.intelligence.observations import Observation, EvidenceSpan
from backend.intelligence.claims import Claim
from backend.intelligence.lineage import SourceLineage


def test_verifier_no_evidence():
    result = EvidenceVerifier().verify_claim(Claim.create("c1", "Test claim"), (), {}, {})
    assert result.status == ClaimStatus.UNKNOWN
    assert "no evidence" in result.reasons[0]


def test_verifier_supported_single_source():
    verifier = EvidenceVerifier()
    obs = Observation.create("o1", "s1", "https://example.com", "The answer is yes.")
    cert = create_certificate(obs, EvidenceSpan("o1", 16, 18))
    result = verifier.verify_claim(Claim.create("c1", "Test claim"), (cert,), {"o1": obs}, {"s1": SourceLineage("s1", "family-a")})
    assert result.status == ClaimStatus.SUPPORTED
    assert result.independent_corroboration_count == 1
    assert len(result.supporting_evidence) == 1


def test_verifier_corroborated_multiple_families():
    verifier = EvidenceVerifier()
    obs1 = Observation.create("o1", "s1", "https://example.com", "The answer is yes.")
    obs2 = Observation.create("o2", "s2", "https://other.com", "Yes, that is correct.")
    cert1 = create_certificate(obs1, EvidenceSpan("o1", 16, 18))
    cert2 = create_certificate(obs2, EvidenceSpan("o2", 0, 3))
    result = verifier.verify_claim(
        Claim.create("c1", "Test claim"), (cert1, cert2), {"o1": obs1, "o2": obs2},
        {"s1": SourceLineage("s1", "family-a"), "s2": SourceLineage("s2", "family-b")},
    )
    assert result.status == ClaimStatus.CORROBORATED
    assert result.independent_corroboration_count == 2


def test_verifier_stale_evidence():
    old_time = datetime.now(timezone.utc) - timedelta(days=31)
    obs = Observation("o1", "s1", "https://example.com", "Old evidence.", old_time)
    cert = create_certificate(obs, EvidenceSpan("o1", 0, 3))
    result = EvidenceVerifier().verify_claim(Claim.create("c1", "Test claim"), (cert,), {"o1": obs}, {"s1": SourceLineage("s1", "family-a")})
    assert result.status == ClaimStatus.STALE
    assert "stale" in result.reasons[0].lower()


def test_verifier_inaccessible_observation():
    obs = Observation.create("o1", "s1", "https://example.com", "Content")
    cert = create_certificate(obs, EvidenceSpan("o1", 0, 7))
    result = EvidenceVerifier().verify_claim(Claim.create("c1", "Test claim"), (cert,), {}, {})
    assert result.status == ClaimStatus.INACCESSIBLE
    assert "not found" in result.reasons[0]
