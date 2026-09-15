from datetime import datetime, timedelta, timezone

from backend.evidence_certificate import create_certificate
from backend.intelligence.evidence import EvidenceRecord
from backend.intelligence.observations import EvidenceSpan, Observation
from backend.intelligence.qualification import create_qualification_receipt


def _inputs(*, ttl=None, result="useful", contradicts=()):
    now = datetime(2026, 9, 15, tzinfo=timezone.utc)
    observed_at = now - timedelta(seconds=5) if ttl is not None else now
    observation = Observation.create(observation_id="obs-qual-1", source_url="https://example.com/product", content="The product has 16 GB RAM.", observed_at=observed_at)
    certificate = create_certificate(observation, EvidenceSpan("obs-qual-1", 4, 22))
    record = EvidenceRecord(evidence_id="ev-qual-1", claim="RAM capacity", entity="Product X", source_url="https://example.com/product", source_family="manufacturer", observed_at=observed_at, result=result, confidence=0.99, freshness_ttl_seconds=ttl, contradicts=tuple(contradicts))
    return now, record, observation, certificate


def test_successful_qualification_is_fully_bound():
    now, record, observation, certificate = _inputs()
    receipt = create_qualification_receipt(record, observation, certificate, field_authority="manufacturer_declaration", authority_allowed=True, evaluation_passed=True, now=now)
    assert receipt.schema == "evidence-qualification-receipt/v1"
    assert receipt.qualified is True
    assert receipt.freshness_ok is True
    assert receipt.contradiction_state == "none"
    assert receipt.evaluation_status == "passed"
    assert receipt.evidence_digest == certificate.content_hash
    assert receipt.source_identity.startswith("manufacturer|")
    assert receipt.reasons == ()


def test_confidence_and_provenance_do_not_override_missing_authority():
    now, record, observation, certificate = _inputs()
    receipt = create_qualification_receipt(record, observation, certificate, field_authority="", authority_allowed=True, evaluation_passed=True, now=now)
    assert receipt.qualified is False
    assert "field authority is missing" in receipt.reasons


def test_disallowed_authority_fails_closed_even_with_high_confidence():
    now, record, observation, certificate = _inputs()
    receipt = create_qualification_receipt(record, observation, certificate, field_authority="community_experience", authority_allowed=False, evaluation_passed=True, now=now)
    assert receipt.qualified is False
    assert "field authority is not allowed for this claim" in receipt.reasons


def test_failed_evaluation_fails_closed():
    now, record, observation, certificate = _inputs()
    receipt = create_qualification_receipt(record, observation, certificate, field_authority="manufacturer_declaration", authority_allowed=True, evaluation_passed=False, now=now)
    assert receipt.qualified is False
    assert receipt.evaluation_status == "failed"
    assert "evaluation did not pass" in receipt.reasons


def test_stale_evidence_fails_closed():
    now, record, observation, certificate = _inputs(ttl=1)
    receipt = create_qualification_receipt(record, observation, certificate, field_authority="manufacturer_declaration", authority_allowed=True, evaluation_passed=True, now=now)
    assert receipt.qualified is False
    assert receipt.freshness_ok is False
    assert "evidence is stale" in receipt.reasons


def test_contradictory_evidence_fails_closed():
    now, record, observation, certificate = _inputs(contradicts=("ev-other",))
    receipt = create_qualification_receipt(record, observation, certificate, field_authority="manufacturer_declaration", authority_allowed=True, evaluation_passed=True, now=now)
    assert receipt.qualified is False
    assert receipt.contradiction_state == "contradictory"
    assert "evidence is contradictory" in receipt.reasons


def test_non_useful_result_fails_closed():
    now, record, observation, certificate = _inputs(result="blocked")
    receipt = create_qualification_receipt(record, observation, certificate, field_authority="manufacturer_declaration", authority_allowed=True, evaluation_passed=True, now=now)
    assert receipt.qualified is False
    assert "evidence result is blocked" in receipt.reasons


def test_invalid_certificate_fails_closed():
    now, record, observation, certificate = _inputs()
    invalid = certificate.__class__(certificate.observation_id, certificate.source_url, certificate.content_hash, certificate.span_start, certificate.span_end, certificate.span_text, False)
    receipt = create_qualification_receipt(record, observation, invalid, field_authority="manufacturer_declaration", authority_allowed=True, evaluation_passed=True, now=now)
    assert receipt.qualified is False
    assert "evidence certificate verification failed" in receipt.reasons


def test_naive_observed_at_is_normalized_to_utc_for_freshness():
    now = datetime(2026, 9, 15, 12, 0, 0, tzinfo=timezone.utc)
    observed = datetime(2026, 9, 15, 11, 59, 58)
    observation = Observation.create(observation_id="obs-qual-naive", source_url="https://example.com/product", content="The product has 16 GB RAM.", observed_at=observed)
    certificate = create_certificate(observation, EvidenceSpan("obs-qual-naive", 4, 22))
    record = EvidenceRecord(evidence_id="ev-qual-naive", claim="RAM capacity", entity="Product X", source_url="https://example.com/product", source_family="manufacturer", observed_at=observed, freshness_ttl_seconds=10)
    receipt = create_qualification_receipt(record, observation, certificate, field_authority="manufacturer_declaration", authority_allowed=True, evaluation_passed=True, now=now)
    assert receipt.freshness_ok is True
    assert receipt.qualified is True
