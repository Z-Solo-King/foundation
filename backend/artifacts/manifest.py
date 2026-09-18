from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
from typing import Any


_HEX64 = set("0123456789abcdef")


def _validate_hash(value: str | None, name: str) -> None:
    if value is None:
        return
    normalized = value.lower()
    if len(normalized) != 64 or any(char not in _HEX64 for char in normalized):
        raise ValueError(f"{name} must be a SHA-256 hex fingerprint")


def _canonical_identity_payload(manifest: "ArtifactManifest") -> dict[str, Any]:
    return {
        "schema_version": manifest.schema_version,
        "request_fingerprint": manifest.request_fingerprint,
        "policy_version": manifest.policy_version,
        "router_version": manifest.router_version,
        "planner_version": manifest.planner_version,
        "retriever_version": manifest.retriever_version,
        "mapper_version": manifest.mapper_version,
        "extractor_version": manifest.extractor_version,
        "adapter_version": manifest.adapter_version,
        "provider_model_identity": manifest.provider_model_identity,
        "source_fingerprints": list(manifest.source_fingerprints),
        "observed_at": manifest.observed_at.isoformat() if manifest.observed_at else None,
        "freshness_state": manifest.freshness_state,
        "budget_allocated": manifest.budget_allocated,
        "budget_consumed": manifest.budget_consumed,
        "result_digest": manifest.result_digest,
    }


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
    request_fingerprint: str | None = None
    router_version: str | None = None
    planner_version: str | None = None
    retriever_version: str | None = None
    mapper_version: str | None = None
    extractor_version: str | None = None
    adapter_version: str | None = None
    provider_model_identity: str | None = None
    source_fingerprints: tuple[str, ...] = ()
    observed_at: datetime | None = None
    freshness_state: str | None = None
    budget_allocated: int = 0
    budget_consumed: int = 0

    def __post_init__(self) -> None:
        if not self.artifact_id.strip() or not self.filename.strip() or not self.format.strip():
            raise ValueError("artifact identity fields are required")
        if not self.schema_version.strip():
            raise ValueError("schema_version is required")
        if not self.provenance.strip():
            raise ValueError("provenance is required")
        if self.created_at.tzinfo is None:
            raise ValueError("created_at must be timezone-aware")
        _validate_hash(self.content_hash, "content_hash")
        _validate_hash(self.execution_fingerprint, "execution_fingerprint")
        _validate_hash(self.result_digest, "result_digest")
        _validate_hash(self.request_fingerprint, "request_fingerprint")
        for fingerprint in self.source_fingerprints:
            _validate_hash(fingerprint, "source_fingerprint")
        for value, name in (
            (self.router_version, "router_version"),
            (self.planner_version, "planner_version"),
            (self.retriever_version, "retriever_version"),
            (self.mapper_version, "mapper_version"),
            (self.extractor_version, "extractor_version"),
            (self.adapter_version, "adapter_version"),
            (self.provider_model_identity, "provider_model_identity"),
        ):
            if value is not None and not value.strip():
                raise ValueError(f"{name} must be non-empty when provided")
        if self.observed_at is not None and self.observed_at.tzinfo is None:
            raise ValueError("observed_at must be timezone-aware")
        if self.freshness_state is not None and self.freshness_state not in {"fresh", "stale", "unknown", "future"}:
            raise ValueError("freshness_state is invalid")
        if self.budget_allocated < 0 or self.budget_consumed < 0:
            raise ValueError("budget values must be non-negative")
        if self.budget_consumed > self.budget_allocated:
            raise ValueError("budget_consumed cannot exceed budget_allocated")
        object.__setattr__(self, "source_fingerprints", tuple(sorted(self.source_fingerprints)))

    @property
    def reproducibility_id(self) -> str:
        payload = json.dumps(
            _canonical_identity_payload(self),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def create_manifest(
    artifact_id,
    filename,
    format,
    content: bytes,
    provenance,
    *,
    execution_fingerprint: str | None = None,
    policy_version: str | None = None,
    result_digest: str | None = None,
    request_fingerprint: str | None = None,
    router_version: str | None = None,
    planner_version: str | None = None,
    retriever_version: str | None = None,
    mapper_version: str | None = None,
    extractor_version: str | None = None,
    adapter_version: str | None = None,
    provider_model_identity: str | None = None,
    source_fingerprints: tuple[str, ...] = (),
    observed_at: datetime | None = None,
    freshness_state: str | None = None,
    budget_allocated: int = 0,
    budget_consumed: int = 0,
    created_at: datetime | None = None,
):
    content_hash = hashlib.sha256(content).hexdigest()
    return ArtifactManifest(
        artifact_id=artifact_id,
        filename=filename,
        format=format,
        content_hash=content_hash,
        created_at=created_at or datetime.now(timezone.utc),
        provenance=provenance,
        execution_fingerprint=execution_fingerprint,
        policy_version=policy_version,
        result_digest=result_digest or content_hash,
        request_fingerprint=request_fingerprint,
        router_version=router_version,
        planner_version=planner_version,
        retriever_version=retriever_version,
        mapper_version=mapper_version,
        extractor_version=extractor_version,
        adapter_version=adapter_version,
        provider_model_identity=provider_model_identity,
        source_fingerprints=source_fingerprints,
        observed_at=observed_at,
        freshness_state=freshness_state,
        budget_allocated=budget_allocated,
        budget_consumed=budget_consumed,
    )
