import pytest

from backend.intelligence.uncertainty import (
    AbstentionReason,
    ClaimUncertainty,
    UncertaintyState,
    classify_claim_uncertainty,
    uncertainty_from_result,
)
from backend.intelligence.verifier import ClaimStatus


def test_uncertainty_classification_is_deterministic():
    assert classify_claim_uncertainty(
        "c1", ClaimStatus.CORROBORATED,
        evidence_sufficient=True, freshness_ok=True, independent_sources=2,
    ).state is UncertaintyState.SUPPORTED
    assert classify_claim_uncertainty(
        "c2", ClaimStatus.PARTIAL,
        evidence_sufficient=True, freshness_ok=True, independent_sources=1,
    ).state is UncertaintyState.QUALIFIED


@pytest.mark.parametrize(
    "status,kwargs,reason",
    [
        (ClaimStatus.UNKNOWN, dict(evidence_sufficient=False, freshness_ok=True, independent_sources=0), AbstentionReason.INSUFFICIENT_EVIDENCE),
        (ClaimStatus.INACCESSIBLE, dict(evidence_sufficient=True, freshness_ok=True, independent_sources=0), AbstentionReason.INACCESSIBLE_EVIDENCE),
        (ClaimStatus.STALE, dict(evidence_sufficient=True, freshness_ok=False, independent_sources=1), AbstentionReason.STALE_EVIDENCE),
        ("future", dict(evidence_sufficient=True, freshness_ok=True, independent_sources=1), AbstentionReason.OUT_OF_SCOPE),
    ],
)
def test_uncertainty_abstains_with_explicit_reason(status, kwargs, reason):
    result = classify_claim_uncertainty("c1", status, **kwargs)
    assert result.state is UncertaintyState.ABSTAIN
    assert result.abstention_reason is reason


def test_contradiction_remains_distinct_from_abstention():
    result = classify_claim_uncertainty(
        "c1", ClaimStatus.CONTRADICTED,
        evidence_sufficient=True, freshness_ok=True, independent_sources=2,
    )
    assert result.state is UncertaintyState.CONTRADICTED
    assert result.abstention_reason is None


def test_uncertainty_invariants_fail_closed():
    with pytest.raises(ValueError, match="claim_id"):
        ClaimUncertainty("", UncertaintyState.UNKNOWN, False, True, 0).validate()
    with pytest.raises(ValueError, match="abstention requires"):
        ClaimUncertainty("c1", UncertaintyState.ABSTAIN, False, True, 0).validate()
    with pytest.raises(ValueError, match="cannot carry"):
        ClaimUncertainty("c1", UncertaintyState.SUPPORTED, True, True, 1, AbstentionReason.OUT_OF_SCOPE).validate()
    with pytest.raises(ValueError, match="non-negative"):
        ClaimUncertainty("c1", UncertaintyState.SUPPORTED, True, True, -1).validate()


def test_evidence_count_derives_sufficiency_without_becoming_authority():
    result = uncertainty_from_result(
        "c1", ClaimStatus.UNKNOWN, evidence_count=0,
        freshness_ok=True, independent_sources=0,
        population_revision="eval-v1",
    )
    assert result.state is UncertaintyState.ABSTAIN
    assert result.population_revision == "eval-v1"
