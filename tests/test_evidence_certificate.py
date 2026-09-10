from backend.content_integrity import sha256_text
from backend.evidence import EvidenceSpan, Observation
from backend.evidence_certificate import create_certificate, verify_certificate


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
    assert verify_certificate(observation, certificate) is True


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
