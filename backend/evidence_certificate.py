from dataclasses import dataclass

from backend.evidence import EvidenceSpan, Observation
from backend.content_integrity import sha256_text


@dataclass(frozen=True)
class EvidenceCertificate:
    observation_id: str
    source_url: str
    content_hash: str
    span_start: int
    span_end: int
    span_text: str


def create_certificate(
    observation: Observation,
    span: EvidenceSpan,
) -> EvidenceCertificate:
    text = span.text_from(observation)

    return EvidenceCertificate(
        observation_id=observation.observation_id,
        source_url=observation.source_url,
        content_hash=sha256_text(observation.content),
        span_start=span.start,
        span_end=span.end,
        span_text=text,
    )


def verify_certificate(
    observation: Observation,
    certificate: EvidenceCertificate,
) -> bool:
    if observation.observation_id != certificate.observation_id:
        return False

    if observation.source_url != certificate.source_url:
        return False

    if sha256_text(observation.content) != certificate.content_hash:
        return False

    span = EvidenceSpan(
        observation_id=certificate.observation_id,
        start=certificate.span_start,
        end=certificate.span_end,
    )

    return span.text_from(observation) == certificate.span_text
