from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib


@dataclass(frozen=True)
class ArtifactManifest:
    artifact_id: str
    filename: str
    format: str
    content_hash: str
    created_at: datetime
    provenance: str


def create_manifest(artifact_id, filename, format, content: bytes, provenance):
    return ArtifactManifest(
        artifact_id,
        filename,
        format,
        hashlib.sha256(content).hexdigest(),
        datetime.now(timezone.utc),
        provenance,
    )
