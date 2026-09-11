from dataclasses import dataclass

from .integrity import sha256_text
from .observations import EvidenceSpan, Observation


@dataclass(frozen=True)
class EvidenceCertificate:
    observation_id: str
    source_id: str
    source_url: str
    content_hash: str
    span_start: int
    span_end: int
    span_text: str
    structurally_valid: bool


def create_certificate(observation, span):
    return EvidenceCertificate(
        observation.observation_id,
        observation.source_id,
        observation.source_url,
        sha256_text(observation.content),
        span.start,
        span.end,
        span.text_from(observation),
        True,
    )


def verify_certificate(observation, certificate):
    if not certificate.structurally_valid:
        return False
    if observation.observation_id != certificate.observation_id:
        return False
    if observation.source_id != certificate.source_id:
        return False
    if observation.source_url != certificate.source_url:
        return False
    if sha256_text(observation.content) != certificate.content_hash:
        return False

    try:
        text = EvidenceSpan(
            certificate.observation_id,
            certificate.span_start,
            certificate.span_end,
        ).text_from(observation)
    except ValueError:
        return False

    return text == certificate.span_text
