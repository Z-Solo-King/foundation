from dataclasses import replace
from datetime import datetime, timedelta, timezone

import pytest

from backend.content_integrity import sha256_text
from backend.intelligence.observations import EvidenceSpan, Observation
from backend.evidence_certificate import create_certificate, verify_certificate


def test_evidence_certificate():
    observation = Observation.create(
        observation_id="obs-002",
        source_url="https://example.com",
        content="The system stores evidence.",
    )
    span = EvidenceSpan("obs-002", 18, 26)
    certificate = create_certificate(observation, span)
    assert certificate.content_hash == sha256_text(observation.content)
    assert certificate.span_text == "evidence"
    assert verify_certificate(observation, certificate) is True


def test_certificate_detects_changed_content():
    observation = Observation.create(
        observation_id="obs-003",
        source_url="https://example.com",
        content="The system stores evidence.",
    )
    span = EvidenceSpan("obs-003", 18, 26)
    certificate = create_certificate(observation, span)
    changed = Observation(
        observation_id="obs-003",
        source_url="https://example.com",
        content="The system stores different facts.",
        observed_at=observation.observed_at,
    )
    assert verify_certificate(changed, certificate) is False


def test_enriched_certificate_binds_document_lineage_extractor_and_replay_metadata():
    observation = Observation.create(
        observation_id="obs-enriched",
        source_id="source-1",
        source_url="https://example.com",
        content="The system stores evidence.",
        document_version_id="doc-v3",
        source_family_id="family-a",
        extractor_version="extractor-v2",
    )
    span = EvidenceSpan("obs-enriched", 18, 26)
    start = datetime(2026, 9, 1, tzinfo=timezone.utc)
    end = start + timedelta(days=1)
    certificate = create_certificate(
        observation,
        span,
        mapper_version="mapper-v4",
        replay_fingerprint="replay-1",
        retention_state="retained",
        temporal_scope_start=start,
        temporal_scope_end=end,
    )
    assert certificate.document_version_id == "doc-v3"
    assert certificate.source_family_id == "family-a"
    assert certificate.extractor_version == "extractor-v2"
    assert certificate.mapper_version == "mapper-v4"
    assert certificate.replay_fingerprint == "replay-1"
    assert certificate.retention_state == "retained"
    assert verify_certificate(observation, certificate)


def test_enriched_certificate_rejects_temporal_and_identity_guards():
    observation = Observation.create(
        observation_id="obs-005",
        source_url="https://example.com",
        content="The system stores evidence.",
    )
    certificate = create_certificate(observation, EvidenceSpan("obs-005", 18, 26))
    now = datetime.now(timezone.utc)
    with pytest.raises(ValueError):
        replace(certificate, temporal_scope_start=now, temporal_scope_end=now - timedelta(seconds=1)).validate()
    with pytest.raises(ValueError):
        replace(certificate, content_hash="bad").validate()
    with pytest.raises(ValueError):
        replace(certificate, span_start=-1).validate()
    with pytest.raises(ValueError):
        replace(certificate, retention_state="x" * 4097).validate()


def test_certificate_detects_provenance_drift():
    observation = Observation.create(
        observation_id="obs-006",
        source_url="https://example.com",
        content="The system stores evidence.",
        document_version_id="doc-v1",
        source_family_id="family-a",
        extractor_version="extractor-v1",
    )
    certificate = create_certificate(observation, EvidenceSpan("obs-006", 18, 26), retention_state="retained")
    changed_document = Observation(
        observation_id="obs-006",
        source_url="https://example.com",
        content=observation.content,
        observed_at=observation.observed_at,
        document_version_id="doc-v2",
        source_family_id="family-a",
        extractor_version="extractor-v1",
    )
    changed_family = Observation(
        observation_id="obs-006",
        source_url="https://example.com",
        content=observation.content,
        observed_at=observation.observed_at,
        document_version_id="doc-v1",
        source_family_id="family-b",
        extractor_version="extractor-v1",
    )
    changed_extractor = Observation(
        observation_id="obs-006",
        source_url="https://example.com",
        content=observation.content,
        observed_at=observation.observed_at,
        document_version_id="doc-v1",
        source_family_id="family-a",
        extractor_version="extractor-v2",
    )
    assert not verify_certificate(changed_document, certificate)
    assert not verify_certificate(changed_family, certificate)
    assert not verify_certificate(changed_extractor, certificate)


def test_explicitly_invalid_certificate_fails_closed():
    observation = Observation.create(
        observation_id="obs-004",
        source_url="https://example.com",
        content="The system stores evidence.",
    )
    span = EvidenceSpan("obs-004", 18, 26)
    certificate = create_certificate(observation, span)
    invalid = certificate.__class__(
        certificate.observation_id,
        certificate.source_url,
        certificate.content_hash,
        certificate.span_start,
        certificate.span_end,
        certificate.span_text,
        False,
    )
    assert verify_certificate(observation, invalid) is False