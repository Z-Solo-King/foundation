"""Tests for evidence verification."""

import pytest
from datetime import datetime, timezone, timedelta

from backend.intelligence.verifier import EvidenceVerifier, VerificationResult, ClaimStatus
from backend.intelligence.certificates import create_certificate
from backend.intelligence.observations import Observation, EvidenceSpan
from backend.intelligence.claims import Claim
from backend.intelligence.lineage import SourceLineage


def test_verifier_no_evidence():
    """Verifier returns UNKNOWN when no evidence provided."""
    verifier = EvidenceVerifier()
    claim = Claim.create("c1", "Test claim")
    result = verifier.verify_claim(claim, (), {}, {})
    assert result.status == ClaimStatus.UNKNOWN
    assert "no evidence" in result.reasons[0]


def test_verifier_supported_single_source():
    """Verifier returns SUPPORTED with evidence from single source family."""
    verifier = EvidenceVerifier()
    obs = Observation.create("o1", "s1", "https://example.com", "The answer is yes.")
    span = EvidenceSpan("o1", 16, 19)
    cert = create_certificate(obs, span)
    claim = Claim.create("c1", "Test claim")
    
    lineage = SourceLineage("s1", "family-a")
    result = verifier.verify_claim(claim, (cert,), {"o1": obs}, {"s1": lineage})
    
    assert result.status == ClaimStatus.SUPPORTED
    assert result.independent_corroboration_count == 1
    assert len(result.supporting_evidence) == 1


def test_verifier_corroborated_multiple_families():
    """Verifier returns CORROBORATED with evidence from multiple source families."""
    verifier = EvidenceVerifier()
    
    obs1 = Observation.create("o1", "s1", "https://example.com", "The answer is yes.")
    span1 = EvidenceSpan("o1", 16, 19)
    cert1 = create_certificate(obs1, span1)
    
    obs2 = Observation.create("o2", "s2", "https://other.com", "Yes, that is correct.")
    span2 = EvidenceSpan("o2", 0, 3)
    cert2 = create_certificate(obs2, span2)
    
    claim = Claim.create("c1", "Test claim")
    lineage1 = SourceLineage("s1", "family-a")
    lineage2 = SourceLineage("s2", "family-b")
    
    result = verifier.verify_claim(
        claim,
        (cert1, cert2),
        {"o1": obs1, "o2": obs2},
        {"s1": lineage1, "s2": lineage2},
    )
    
    assert result.status == ClaimStatus.CORROBORATED
    assert result.independent_corroboration_count == 2


def test_verifier_stale_evidence():
    """Verifier detects and flags stale evidence."""
    verifier = EvidenceVerifier()
    
    # Create an observation from >30 days ago
    old_time = datetime.now(timezone.utc) - timedelta(days=31)
    obs = Observation(
        "o1", "s1", "https://example.com", "Old evidence.", old_time
    )
    span = EvidenceSpan("o1", 0, 3)
    cert = create_certificate(obs, span)
    
    claim = Claim.create("c1", "Test claim")
    lineage = SourceLineage("s1", "family-a")
    
    result = verifier.verify_claim(claim, (cert,), {"o1": obs}, {"s1": lineage})
    
    assert result.status == ClaimStatus.STALE
    assert "stale" in result.reasons[0].lower()


def test_verifier_inaccessible_observation():
    """Verifier returns INACCESSIBLE when observation is missing."""
    verifier = EvidenceVerifier()
    
    # Create certificate for observation that doesn't exist
    obs = Observation.create("o1", "s1", "https://example.com", "Content")
    span = EvidenceSpan("o1", 0, 7)
    cert = create_certificate(obs, span)
    
    claim = Claim.create("c1", "Test claim")
    
    # Pass empty observations dict
    result = verifier.verify_claim(claim, (cert,), {}, {})
    
    assert result.status == ClaimStatus.INACCESSIBLE
    assert "not found" in result.reasons[0]
