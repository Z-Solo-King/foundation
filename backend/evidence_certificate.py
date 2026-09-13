from dataclasses import dataclass
from datetime import datetime

from backend.intelligence.observations import EvidenceSpan, Observation
from backend.content_integrity import sha256_text


@dataclass(frozen=True)
class EvidenceCertificate:
    observation_id: str
    source_url: str
    content_hash: str
    span_start: int
    span_end: int
    span_text: str
    structurally_valid: bool = True
    document_version_id: str | None = None
    temporal_scope_start: datetime | None = None
    temporal_scope_end: datetime | None = None
    source_family_id: str | None = None
    extractor_version: str | None = None
    mapper_version: str | None = None
    retention_state: str | None = None
    replay_fingerprint: str | None = None

    def validate(self) -> None:
        if not self.observation_id.strip() or not self.source_url.strip():
            raise ValueError("certificate identity must not be empty")
        if not self.content_hash.strip() or len(self.content_hash) != 64:
            raise ValueError("certificate content_hash must be a SHA-256 hex digest")
        if self.span_start < 0 or self.span_end < self.span_start:
            raise ValueError("certificate span bounds are invalid")
        for name in (
            "document_version_id", "source_family_id", "extractor_version", "mapper_version",
            "retention_state", "replay_fingerprint",
        ):
            value = getattr(self, name)
            if value is not None and (not isinstance(value, str) or len(value) > 4096):
                raise ValueError(f"{name} exceeds bounded length")
        if self.temporal_scope_start and self.temporal_scope_end and self.temporal_scope_end < self.temporal_scope_start:
            raise ValueError("temporal scope end precedes start")


def create_certificate(
    observation: Observation,
    span: EvidenceSpan,
    *,
    mapper_version: str | None = None,
    replay_fingerprint: str | None = None,
    temporal_scope_start: datetime | None = None,
    temporal_scope_end: datetime | None = None,
) -> EvidenceCertificate:
    text = span.text_from(observation)

    certificate = EvidenceCertificate(
        observation_id=observation.observation_id,
        source_url=observation.source_url,
        content_hash=sha256_text(observation.content),
        span_start=span.start,
        span_end=span.end,
        span_text=text,
        document_version_id=observation.document_version_id,
        temporal_scope_start=temporal_scope_start,
        temporal_scope_end=temporal_scope_end,
        source_family_id=observation.source_family_id,
        extractor_version=observation.extractor_version,
        mapper_version=mapper_version,
        retention_state=observation.policy_state,
        replay_fingerprint=replay_fingerprint,
    )
    certificate.validate()
    return certificate


def verify_certificate(
    observation: Observation,
    certificate: EvidenceCertificate,
) -> bool:
    try:
        certificate.validate()
    except ValueError:
        return False

    if not certificate.structurally_valid:
        return False

    if observation.observation_id != certificate.observation_id:
        return False

    if observation.source_url != certificate.source_url:
        return False

    if sha256_text(observation.content) != certificate.content_hash:
        return False

    if observation.document_version_id != certificate.document_version_id:
        return False
    if observation.source_family_id != certificate.source_family_id:
        return False
    if observation.extractor_version != certificate.extractor_version:
        return False
    if observation.policy_state != certificate.retention_state:
        return False

    span = EvidenceSpan(
        observation_id=certificate.observation_id,
        start=certificate.span_start,
        end=certificate.span_end,
    )

    return span.text_from(observation) == certificate.span_text