from datetime import datetime, timezone

from backend.evaluation.entailment import EntailmentStatus, adjudicate_ambiguous, verify_claim_entailment
from backend.intelligence.observations import EvidenceSpan, Observation


def obs(text="Product costs $10 per month in India."):
    return Observation("o1", "https://example.com", text, datetime.now(timezone.utc))


def test_exact_claim_is_supported():
    observation = obs()
    span = EvidenceSpan("o1", 0, len(observation.content))
    result = verify_claim_entailment("Product costs $10 per month in India.", observation, span)
    assert result.status == EntailmentStatus.SUPPORTED
    assert result.accepted


def test_negation_mismatch_is_unsupported():
    observation = obs("Product is not available in India.")
    span = EvidenceSpan("o1", 0, len(observation.content))
    result = verify_claim_entailment("Product is available in India.", observation, span)
    assert result.status == EntailmentStatus.UNSUPPORTED


def test_invalid_span_fails_closed():
    observation = obs()
    result = verify_claim_entailment("Product costs $10", observation, EvidenceSpan("o1", 999, 1000))
    assert result.status == EntailmentStatus.INVALID


def test_ambiguous_case_can_be_adjudicated_explicitly():
    observation = obs("Product has a monthly price in India.")
    span = EvidenceSpan("o1", 0, len(observation.content))
    result = verify_claim_entailment("Product costs $10 per month in India.", observation, span, ambiguous_threshold=0.4, supported_threshold=0.99)
    assert result.status == EntailmentStatus.AMBIGUOUS
    assert adjudicate_ambiguous(result, True).accepted
    assert not adjudicate_ambiguous(result, False).accepted
