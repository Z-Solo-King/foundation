import pytest

from backend.content_integrity import sha256_text
from backend.intelligence.observations import EvidenceSpan, Observation
from backend.evidence_certificate import EvidenceCertificate, create_certificate, verify_certificate
from backend.intelligence.certificates import EvidenceCertificate as IntelligenceEvidenceCertificate


def test_evidence_certificate_is_canonical_across_import_paths():
    assert IntelligenceEvidenceCertificate is EvidenceCertificate


def test_evidence_certificate():
    observation = Observation.create(
        observation_id="obs-002",
        source_url="https://example.com",
        content="The system stores evidence.",
    )

    span = EvidenceSpan(
        observation_id="obs-002",
        start=18,
        end=26,
    )

    certificate = create_certificate(observation, span)

    assert certificate.content_hash == sha256_text(observation.content)
    assert certificate.span_text == "evidence"
    assert certificate.source_id is None
    assert verify_certificate(observation, certificate) is True


def test_omitted_structural_validity_defaults_to_true():
    certificate = EvidenceCertificate(
        "obs-default",
        "https://example.com",
        "a" * 64,
        0,
        5,
        "hello",
    )
    assert certificate.structurally_valid is True


def test_source_id_compatibility_remains_bound_when_present():
    observation = Observation.create(
        observation_id="obs-002-source",
        source_id="source-1",
        source_url="https://example.com",
        content="The system stores evidence.",
    )
    span = EvidenceSpan("obs-002-source", 18, 26)
    certificate = create_certificate(observation, span)
    assert certificate.source_id == "source-1"
    assert verify_certificate(observation, certificate) is True

    wrong_source = Observation(
        observation_id=observation.observation_id,
        source_id="source-2",
        source_url=observation.source_url,
        content=observation.content,
        observed_at=observation.observed_at,
    )
    assert verify_certificate(wrong_source, certificate) is False


def test_certificate_detects_changed_content():
    observation = Observation.create(
        observation_id="obs-003",
        source_url="https://example.com",
        content="The system stores evidence.",
    )

    span = EvidenceSpan(
        observation_id="obs-003",
        start=18,
        end=26,
    )

    certificate = create_certificate(observation, span)

    changed = Observation(
        observation_id="obs-003",
        source_url="https://example.com",
        content="The system stores different facts.",
        observed_at=observation.observed_at,
    )

    assert verify_certificate(changed, certificate) is False


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


def test_certificate_rejects_blank_observation_id():
    with pytest.raises(ValueError, match="observation_id"):
        EvidenceCertificate("", "https://example.com", "a" * 64, 0, 1, "x")


def test_certificate_rejects_blank_source_url():
    with pytest.raises(ValueError, match="source_url"):
        EvidenceCertificate("obs", "", "a" * 64, 0, 1, "x")


def test_certificate_rejects_non_string_source_url():
    with pytest.raises(ValueError, match="source_url"):
        EvidenceCertificate("obs", 123, "a" * 64, 0, 1, "x")


def test_certificate_rejects_blank_content_hash():
    with pytest.raises(ValueError, match="content_hash"):
        EvidenceCertificate("obs", "https://example.com", "", 0, 1, "x")


def test_certificate_rejects_non_integer_span_bounds():
    with pytest.raises(TypeError, match="span_start"):
        EvidenceCertificate("obs", "https://example.com", "a" * 64, "0", 1, "x")
    with pytest.raises(TypeError, match="span_end"):
        EvidenceCertificate("obs", "https://example.com", "a" * 64, 0, "1", "x")


def test_certificate_rejects_non_string_span_text():
    with pytest.raises(TypeError, match="span_text"):
        EvidenceCertificate("obs", "https://example.com", "a" * 64, 0, 1, 123)


def test_certificate_rejects_non_boolean_validity():
    with pytest.raises(TypeError, match="structurally_valid"):
        EvidenceCertificate("obs", "https://example.com", "a" * 64, 0, 1, "x", 1)


def test_certificate_rejects_non_string_source_id():
    with pytest.raises(TypeError, match="source_id"):
        EvidenceCertificate(
            "obs",
            "https://example.com",
            "a" * 64,
            0,
            1,
            "x",
            source_id=1,
        )


def test_certificate_rejects_invalid_positional_arity_and_mixed_arguments():
    with pytest.raises(ValueError):
        EvidenceCertificate("obs")
    with pytest.raises(TypeError, match="either positional or named"):
        EvidenceCertificate("obs", "https://example.com", source_url="https://example.com")
