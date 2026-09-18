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
    schema_version: str = "artifact-manifest/v1"
    execution_fingerprint: str | None = None
    policy_version: str | None = None
    result_digest: str | None = None


def create_manifest(
    artifact_id,
    filename,
    format,
    content: bytes,
    provenance,
    *,
    execution_fingerprint: str | None = None,
    policy_version: str | None = None,
):
    content_hash = hashlib.sha256(content).hexdigest()
    return ArtifactManifest(
        artifact_id=artifact_id,
        filename=filename,
        format=format,
        content_hash=content_hash,
        created_at=datetime.now(timezone.utc),
        provenance=provenance,
        execution_fingerprint=execution_fingerprint,
        policy_version=policy_version,
        result_digest=content_hash,
    )
