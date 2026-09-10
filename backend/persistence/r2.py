"""Cloudflare R2 persistence layer for large artifacts.

R2 stores raw documents, PDFs, media, extracted artifacts, and manifests.
Metadata and linkage stay in D1.

Lifecycle and retention policies are enforced at R2 and D1 layers.
"""

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class R2Artifact:
    """Reference to an artifact stored in R2."""
    artifact_id: str
    bucket: str  # project-evidence, project-artifacts
    key: str  # path within bucket
    content_type: str
    size_bytes: int
    created_at: datetime
    content_hash: str  # SHA-256
    retention_days: int | None = None  # None = permanent


@dataclass(frozen=True)
class ArtifactManifest:
    """Manifest describing artifact contents and structure."""
    artifact_id: str
    name: str
    description: str
    artifact_type: str  # pdf, html, json, archive, media
    metadata: dict[str, str]  # type hints, encoding, pages, etc.


class R2Repository:
    """Thin abstraction over R2 storage.
    
    In production, wraps Cloudflare R2 API.
    For testing, uses in-memory storage.
    """
    
    def __init__(self):
        self._artifacts: dict[str, tuple[R2Artifact, bytes]] = {}
        self._manifests: dict[str, ArtifactManifest] = {}
    
    def upload(self, artifact: R2Artifact, content: bytes) -> R2Artifact:
        """Upload an artifact to R2."""
        if artifact.artifact_id in self._artifacts:
            raise ValueError(f"artifact {artifact.artifact_id} already exists")
        if artifact.size_bytes != len(content):
            raise ValueError("artifact size mismatch")
        self._artifacts[artifact.artifact_id] = (artifact, content)
        return artifact
    
    def download(self, artifact_id: str) -> tuple[R2Artifact, bytes] | None:
        """Download an artifact from R2."""
        return self._artifacts.get(artifact_id)
    
    def delete(self, artifact_id: str) -> None:
        """Delete an artifact (enforce retention policy)."""
        if artifact_id in self._artifacts:
            del self._artifacts[artifact_id]
    
    def add_manifest(self, manifest: ArtifactManifest) -> ArtifactManifest:
        """Store an artifact manifest."""
        if manifest.artifact_id in self._manifests:
            raise ValueError(f"manifest {manifest.artifact_id} already exists")
        self._manifests[manifest.artifact_id] = manifest
        return manifest
    
    def get_manifest(self, artifact_id: str) -> ArtifactManifest | None:
        """Retrieve an artifact manifest."""
        return self._manifests.get(artifact_id)
