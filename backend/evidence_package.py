"""Public-safe validation for trusted research publication packages."""
from __future__ import annotations

import hashlib
import hmac
import json
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class EvidencePackage:
    schema: str
    package_id: str
    research_run_id: str
    source_versions: tuple[str, ...]
    evidence_spans: tuple[str, ...]
    claims: tuple[dict[str, Any], ...]
    synthesis: str
    artifact_digest: str
    signer: str
    signature: str

    def unsigned_payload(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "package_id": self.package_id,
            "research_run_id": self.research_run_id,
            "source_versions": sorted(set(self.source_versions)),
            "evidence_spans": sorted(set(self.evidence_spans)),
            "claims": self.claims,
            "synthesis": self.synthesis,
            "signer": self.signer,
        }

    def canonical_bytes(self) -> bytes:
        return json.dumps(
            self.unsigned_payload(), ensure_ascii=False, sort_keys=True, separators=(",", ":")
        ).encode("utf-8")

    def payload(self) -> dict[str, Any]:
        return {**self.unsigned_payload(), "artifact_digest": self.artifact_digest}

    def validate(self, trust_key: bytes) -> None:
        if self.schema != "evidence-package/v1":
            raise ValueError("unsupported evidence package schema")
        if not self.package_id.strip() or not self.research_run_id.strip() or not self.signer.strip():
            raise ValueError("package identity is required")
        if not self.synthesis.strip():
            raise ValueError("synthesis is required")
        if not self.source_versions or not self.evidence_spans or not self.claims:
            raise ValueError("trusted package must contain lineage, evidence and claims")
        if any(not isinstance(item, dict) for item in self.claims):
            raise ValueError("claims must be objects")
        if any(not str(item).strip() for item in self.source_versions + self.evidence_spans):
            raise ValueError("lineage identifiers must be non-empty")
        if len(self.artifact_digest) != 64 or any(c not in "0123456789abcdef" for c in self.artifact_digest):
            raise ValueError("artifact_digest must be SHA-256")
        if hashlib.sha256(self.canonical_bytes()).hexdigest() != self.artifact_digest:
            raise ValueError("artifact digest mismatch")
        if not trust_key:
            raise ValueError("publication trust key is unavailable")
        expected = hmac.new(trust_key, self.canonical_bytes(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(expected, self.signature):
            raise ValueError("evidence package signature is invalid")


def parse_trusted_package(payload: object, trust_key: bytes) -> EvidencePackage:
    if not isinstance(payload, dict):
        raise ValueError("evidence package must be an object")
    raw_claims = payload.get("claims", ())
    raw_sources = payload.get("source_versions", ())
    raw_spans = payload.get("evidence_spans", ())
    if not isinstance(raw_claims, (list, tuple)) or not isinstance(raw_sources, (list, tuple)) or not isinstance(raw_spans, (list, tuple)):
        raise ValueError("claims and lineage fields must be arrays")
    p = EvidencePackage(
        schema=str(payload.get("schema", "")),
        package_id=str(payload.get("package_id", "")),
        research_run_id=str(payload.get("research_run_id", "")),
        source_versions=tuple(str(x) for x in raw_sources),
        evidence_spans=tuple(str(x) for x in raw_spans),
        claims=tuple(raw_claims),
        synthesis=str(payload.get("synthesis", "")),
        artifact_digest=str(payload.get("artifact_digest", "")),
        signer=str(payload.get("signer", "")),
        signature=str(payload.get("signature", "")),
    )
    p.validate(trust_key)
    return p
