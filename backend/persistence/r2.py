"""Legacy R2 compatibility façade.

R2 is not a production storage backend in the current architecture. Production large
artifact persistence is provided by ``backend.persistence.artifacts.B2ArtifactStore``.
This module survives only because historical/public tests and compatibility imports
still refer to the old R2Repository symbols. It is an in-memory compatibility test
double and performs no R2 network I/O.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class R2Artifact:
    """Legacy artifact record retained for compatibility tests only."""
    artifact_id: str
    bucket: str
    key: str
    content_type: str
    size_bytes: int
    created_at: datetime
    content_hash: str
    retention_days: int | None = None


@dataclass(frozen=True)
class ArtifactManifest:
    """Legacy manifest record retained for compatibility tests only."""
    artifact_id: str
    name: str
    description: str
    artifact_type: str
    metadata: dict[str, str]


class R2Repository:
    """Compatibility test double; no production R2 access exists here."""

    def __init__(self):
        self._artifacts: dict[str, tuple[R2Artifact, bytes]] = {}
        self._manifests: dict[str, ArtifactManifest] = {}

    def upload(self, artifact: R2Artifact, content: bytes) -> R2Artifact:
        if artifact.artifact_id in self._artifacts:
            raise ValueError(f"artifact {artifact.artifact_id} already exists")
        if artifact.size_bytes != len(content):
            raise ValueError("artifact size mismatch")
        self._artifacts[artifact.artifact_id] = (artifact, content)
        return artifact

    def download(self, artifact_id: str) -> tuple[R2Artifact, bytes] | None:
        return self._artifacts.get(artifact_id)

    def delete(self, artifact_id: str) -> None:
        self._artifacts.pop(artifact_id, None)

    def add_manifest(self, manifest: ArtifactManifest) -> ArtifactManifest:
        if manifest.artifact_id in self._manifests:
            raise ValueError(f"manifest {manifest.artifact_id} already exists")
        self._manifests[manifest.artifact_id] = manifest
        return manifest

    def get_manifest(self, artifact_id: str) -> ArtifactManifest | None:
        return self._manifests.get(artifact_id)
