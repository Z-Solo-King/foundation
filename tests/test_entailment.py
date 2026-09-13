from dataclasses import replace
from datetime import datetime, timezone

import pytest

from backend.evaluation.entailment import (
    EntailmentResult,
    EntailmentStatus,
    SemanticCalibrationProfile,
    adjudicate_ambiguous,
    adjudicate_semantic_score,
    calibrate_semantic_score,
    verify_claim_entailment,
)
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


def test_semantic_calibration_profile_and_raw_score_guards():
    profile = SemanticCalibrationProfile("cal-v1", raw_low=0.2, raw_high=0.8)
    profile.validate()
    assert calibrate_semantic_score(0.2, profile) == 0.0
    assert calibrate_semantic_score(0.5, profile) == pytest.approx(0.5)
    assert calibrate_semantic_score(0.8, profile) == 1.0
    with pytest.raises(ValueError):
        SemanticCalibrationProfile("").validate()
    with pytest.raises(ValueError):
        SemanticCalibrationProfile("bad", raw_low=.8, raw_high=.2).validate()
    with pytest.raises(ValueError):
        calibrate_semantic_score(-.1, profile)
    with pytest.raises(ValueError):
        calibrate_semantic_score(1.1, profile)


def test_semantic_adjudication_only_resolves_ambiguous_results():
    profile = SemanticCalibrationProfile("cal-v1")
    ambiguous = EntailmentResult(EntailmentStatus.AMBIGUOUS, .65, "needs review")
    assert adjudicate_semantic_score(ambiguous, .95, profile).status == EntailmentStatus.SUPPORTED
    assert adjudicate_semantic_score(ambiguous, .7, profile).status == EntailmentStatus.AMBIGUOUS
    assert adjudicate_semantic_score(ambiguous, .2, profile).status == EntailmentStatus.UNSUPPORTED
    supported = replace(ambiguous, status=EntailmentStatus.SUPPORTED)
    assert adjudicate_semantic_score(supported, .1, profile) == supported