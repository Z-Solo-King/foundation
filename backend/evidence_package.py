"""Public-safe validation for trusted research publication packages."""
from __future__ import annotations
import hashlib, hmac, json
from dataclasses import dataclass
from typing import Any

@dataclass(frozen=True)
class EvidencePackage:
    schema: str; package_id: str; research_run_id: str; source_versions: tuple[str, ...]; evidence_spans: tuple[str, ...]; claims: tuple[dict[str, Any], ...]; synthesis: str; artifact_digest: str; signer: str; signature: str
    def unsigned_payload(self) -> dict[str, Any]:
        return {"schema":self.schema,"package_id":self.package_id,"research_run_id":self.research_run_id,"source_versions":sorted(set(self.source_versions)),"evidence_spans":sorted(set(self.evidence_spans)),"claims":self.claims,"synthesis":self.synthesis,"signer":self.signer}
    def canonical_bytes(self) -> bytes: return json.dumps(self.unsigned_payload(),ensure_ascii=False,sort_keys=True,separators=(",",":")).encode()
    def payload(self) -> dict[str, Any]: return {**self.unsigned_payload(),"artifact_digest":self.artifact_digest}
    def validate(self, trust_key: bytes) -> None:
        if self.schema != "evidence-package/v1": raise ValueError("unsupported evidence package schema")
        if not self.package_id.strip() or not self.research_run_id.strip() or not self.signer.strip(): raise ValueError("package identity is required")
        if not self.synthesis.strip(): raise ValueError("synthesis is required")
        if len(self.artifact_digest)!=64 or any(c not in "0123456789abcdef" for c in self.artifact_digest.lower()): raise ValueError("artifact_digest must be SHA-256")
        if hashlib.sha256(self.canonical_bytes()).hexdigest()!=self.artifact_digest: raise ValueError("artifact digest mismatch")
        if not trust_key: raise ValueError("publication trust key is unavailable")
        expected=hmac.new(trust_key,self.canonical_bytes(),hashlib.sha256).hexdigest()
        if not hmac.compare_digest(expected,self.signature): raise ValueError("evidence package signature is invalid")
        if not self.source_versions or not self.evidence_spans or not self.claims: raise ValueError("trusted package must contain lineage, evidence and claims")

def parse_trusted_package(payload: object, trust_key: bytes) -> EvidencePackage:
    if not isinstance(payload,dict): raise ValueError("evidence package must be an object")
    p=EvidencePackage(schema=str(payload.get("schema","")),package_id=str(payload.get("package_id","")),research_run_id=str(payload.get("research_run_id","")),source_versions=tuple(str(x) for x in payload.get("source_versions",())),evidence_spans=tuple(str(x) for x in payload.get("evidence_spans",())),claims=tuple(x for x in payload.get("claims",()) if isinstance(x,dict)),synthesis=str(payload.get("synthesis","")),artifact_digest=str(payload.get("artifact_digest","")),signer=str(payload.get("signer","")),signature=str(payload.get("signature","")))
    p.validate(trust_key); return p
