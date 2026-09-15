from dataclasses import dataclass, field

from backend.intelligence.integrity import sha256_text
from backend.intelligence.observations import EvidenceSpan, Observation


@dataclass(frozen=True, init=False)
class EvidenceCertificate:
    """Canonical evidence certificate with legacy source-id compatibility."""

    observation_id: str
    source_url: str
    content_hash: str
    span_start: int
    span_end: int
    span_text: str
    structurally_valid: bool = True
    source_id: str | None = field(default=None, compare=True)

    def __init__(
        self,
        observation_id: str,
        *args: object,
        source_url: str | None = None,
        content_hash: str | None = None,
        span_start: int | None = None,
        span_end: int | None = None,
        span_text: str | None = None,
        structurally_valid: bool = True,
        source_id: str | None = None,
    ) -> None:
        if args:
            if any(value is not None for value in (source_url, content_hash, span_start, span_end, span_text)):
                raise TypeError("certificate fields must use either positional or named arguments")
            if len(args) == 5:
                source_url, content_hash, span_start, span_end, span_text = args
            elif len(args) == 6:
                source_url, content_hash, span_start, span_end, span_text, structurally_valid = args
            elif len(args) == 7:
                source_id, source_url, content_hash, span_start, span_end, span_text, structurally_valid = args
            else:
                raise TypeError("EvidenceCertificate expects 6, 7 or 8 positional values")

        if not isinstance(observation_id, str) or not observation_id:
            raise ValueError("observation_id is required")
        if not isinstance(source_url, str) or not source_url:
            raise ValueError("source_url is required")
        if not isinstance(content_hash, str) or not content_hash:
            raise ValueError("content_hash is required")
        if not isinstance(span_start, int) or not isinstance(span_end, int):
            raise TypeError("span_start and span_end must be integers")
        if not isinstance(span_text, str):
            raise TypeError("span_text must be a string")
        if not isinstance(structurally_valid, bool):
            raise TypeError("structurally_valid must be a boolean")
        if source_id is not None and not isinstance(source_id, str):
            raise TypeError("source_id must be a string or None")

        object.__setattr__(self, "observation_id", observation_id)
        object.__setattr__(self, "source_url", source_url)
        object.__setattr__(self, "content_hash", content_hash)
        object.__setattr__(self, "span_start", span_start)
        object.__setattr__(self, "span_end", span_end)
        object.__setattr__(self, "span_text", span_text)
        object.__setattr__(self, "structurally_valid", structurally_valid)
        object.__setattr__(self, "source_id", source_id)


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
        source_id=observation.source_id,
    )


def verify_certificate(
    observation: Observation,
    certificate: EvidenceCertificate,
) -> bool:
    if not certificate.structurally_valid:
        return False
    if observation.observation_id != certificate.observation_id:
        return False
    if observation.source_url != certificate.source_url:
        return False
    if certificate.source_id is not None and observation.source_id != certificate.source_id:
        return False
    if sha256_text(observation.content) != certificate.content_hash:
        return False

    span = EvidenceSpan(
        observation_id=certificate.observation_id,
        start=certificate.span_start,
        end=certificate.span_end,
    )
    return span.text_from(observation) == certificate.span_text
