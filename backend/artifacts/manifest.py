from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
import hashlib
from typing import Mapping


class ArtifactKind(StrEnum):
    FILE = "file"
    CODE = "code"
    DATA = "data"
    DOCUMENT = "document"
    MEDIA = "media"


@dataclass(frozen=True)
class ArtifactManifest:
    artifact_id: str
    filename: str
    format: str
    content_hash: str
    created_at: datetime
    provenance: str
    kind: ArtifactKind = ArtifactKind.FILE
    schema_version: str = "1"
    size_bytes: int = 0
    media_type: str = "application/octet-stream"
    producer: str = ""
    retention_seconds: int | None = None
    metadata: Mapping[str, str] = field(default_factory=dict)

    def validate(self) -> None:
        if not self.artifact_id.strip() or not self.filename.strip() or not self.format.strip():
            raise ValueError("artifact identity fields must not be empty")
        if len(self.content_hash) != 64 or any(char not in "0123456789abcdef" for char in self.content_hash.lower()):
            raise ValueError("content_hash must be a SHA-256 hex digest")
        if self.size_bytes < 0:
            raise ValueError("size_bytes must be non-negative")
        if self.retention_seconds is not None and self.retention_seconds < 0:
            raise ValueError("retention_seconds must be non-negative")
        if not self.schema_version.strip():
            raise ValueError("schema_version must not be empty")
        if not isinstance(self.kind, ArtifactKind):
            raise ValueError("kind must be a supported ArtifactKind")

    def verify_content(self, content: bytes) -> bool:
        return hashlib.sha256(content).hexdigest() == self.content_hash and len(content) == self.size_bytes


def create_manifest(
    artifact_id,
    filename,
    format,
    content: bytes,
    provenance,
    *,
    kind: ArtifactKind = ArtifactKind.FILE,
    schema_version: str = "1",
    media_type: str = "application/octet-stream",
    producer: str = "",
    retention_seconds: int | None = None,
    metadata: Mapping[str, str] | None = None,
):
    manifest = ArtifactManifest(
        artifact_id,
        filename,
        format,
        hashlib.sha256(content).hexdigest(),
        datetime.now(timezone.utc),
        provenance,
        kind=kind,
        schema_version=schema_version,
        size_bytes=len(content),
        media_type=media_type,
        producer=producer,
        retention_seconds=retention_seconds,
        metadata=dict(metadata or {}),
    )
    manifest.validate()
    return manifest