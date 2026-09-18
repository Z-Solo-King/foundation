from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import StrEnum
import hashlib


class SpanMappingState(StrEnum):
    EXACT = "exact"
    MAPPED = "mapped"
    UNMAPPED = "unmapped"
    LOSSY = "lossy"


@dataclass(frozen=True)
class TransformationLineage:
    parent_artifact_id: str
    transformation_type: str
    transformation_version: str
    input_fingerprint: str
    output_fingerprint: str
    span_mapping: SpanMappingState
    transformed_at: datetime
    execution_identity: str | None = None
    language_from: str | None = None
    language_to: str | None = None
    warning: str | None = None

    def validate(self) -> None:
        if not self.parent_artifact_id.strip():
            raise ValueError("parent_artifact_id is required")
        if not self.transformation_type.strip():
            raise ValueError("transformation_type is required")
        if not self.transformation_version.strip():
            raise ValueError("transformation_version is required")
        for value, name in (
            (self.input_fingerprint, "input_fingerprint"),
            (self.output_fingerprint, "output_fingerprint"),
        ):
            if len(value) != 64 or any(ch not in "0123456789abcdef" for ch in value.lower()):
                raise ValueError(f"{name} must be a SHA-256 hex fingerprint")
        if self.transformed_at.tzinfo is None:
            raise ValueError("transformed_at must be timezone-aware")
        if self.span_mapping is SpanMappingState.LOSSY and not (self.warning or "").strip():
            raise ValueError("lossy transformations require an explicit warning")
        if self.span_mapping is SpanMappingState.EXACT and self.input_fingerprint != self.output_fingerprint:
            raise ValueError("exact mapping requires identical input and output fingerprints")


def content_fingerprint(content: bytes | str) -> str:
    payload = content.encode("utf-8") if isinstance(content, str) else bytes(content)
    return hashlib.sha256(payload).hexdigest()


def create_transformation_lineage(
    parent_artifact_id: str,
    transformation_type: str,
    transformation_version: str,
    input_content: bytes | str,
    output_content: bytes | str,
    *,
    span_mapping: SpanMappingState = SpanMappingState.EXACT,
    execution_identity: str | None = None,
    language_from: str | None = None,
    language_to: str | None = None,
    warning: str | None = None,
    transformed_at: datetime | None = None,
) -> TransformationLineage:
    lineage = TransformationLineage(
        parent_artifact_id=parent_artifact_id,
        transformation_type=transformation_type,
        transformation_version=transformation_version,
        input_fingerprint=content_fingerprint(input_content),
        output_fingerprint=content_fingerprint(output_content),
        span_mapping=span_mapping,
        transformed_at=transformed_at or datetime.now(timezone.utc),
        execution_identity=execution_identity,
        language_from=language_from,
        language_to=language_to,
        warning=warning,
    )
    lineage.validate()
    return lineage
