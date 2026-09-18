from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
import hashlib


ARTIFACT_INGESTION_CONTRACT_VERSION = "artifact-ingestion/v1"


class ArtifactIngestionState(StrEnum):
    EXTRACTED = "extracted"
    PARTIAL = "partial"
    UNSUPPORTED = "unsupported"
    BLOCKED = "blocked"


@dataclass(frozen=True)
class IngestionAdapterSpec:
    adapter_id: str
    input_media_types: tuple[str, ...]
    extraction_version: str
    max_bytes: int
    max_depth: int
    deterministic: bool = True
    model_assisted: bool = False

    def validate(self) -> None:
        if not self.adapter_id.strip():
            raise ValueError("adapter_id is required")
        if not self.input_media_types or any(not item.strip() for item in self.input_media_types):
            raise ValueError("input_media_types must contain non-empty values")
        if not self.extraction_version.strip():
            raise ValueError("extraction_version is required")
        if self.max_bytes < 1 or self.max_depth < 1:
            raise ValueError("ingestion resource limits must be positive")
        if not self.deterministic and not self.model_assisted:
            raise ValueError("non-deterministic adapters must declare model assistance")

    @property
    def schema_version(self) -> str:
        return ARTIFACT_INGESTION_CONTRACT_VERSION


@dataclass(frozen=True)
class ArtifactExtractionResult:
    artifact_id: str
    source_fingerprint: str
    output_fingerprint: str | None
    media_type: str
    state: ArtifactIngestionState
    adapter: IngestionAdapterSpec
    warning: str | None = None
    source_language: str | None = None

    def validate(self) -> None:
        self.adapter.validate()
        if not self.artifact_id.strip():
            raise ValueError("artifact_id is required")
        if len(self.source_fingerprint) != 64 or any(ch not in "0123456789abcdef" for ch in self.source_fingerprint.lower()):
            raise ValueError("source_fingerprint must be SHA-256")
        if not self.media_type.strip():
            raise ValueError("media_type is required")
        if self.state in {ArtifactIngestionState.EXTRACTED, ArtifactIngestionState.PARTIAL}:
            if not self.output_fingerprint:
                raise ValueError("successful extraction states require output_fingerprint")
        if self.state is ArtifactIngestionState.UNSUPPORTED and not (self.warning or "").strip():
            raise ValueError("unsupported artifacts require a warning")
        if self.state is ArtifactIngestionState.BLOCKED and self.output_fingerprint is not None:
            raise ValueError("blocked artifacts cannot expose extracted output")
        if self.adapter.model_assisted and not (self.warning or "").strip():
            raise ValueError("model-assisted extraction requires an explicit warning")


def content_fingerprint(content: bytes | str) -> str:
    payload = content.encode("utf-8") if isinstance(content, str) else bytes(content)
    return hashlib.sha256(payload).hexdigest()
