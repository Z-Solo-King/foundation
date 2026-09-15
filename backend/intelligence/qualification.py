from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256

from backend.evidence_certificate import EvidenceCertificate, verify_certificate
from backend.intelligence.evidence import EvidenceRecord
from backend.intelligence.observations import Observation


@dataclass(frozen=True)
class EvidenceQualificationReceipt:
    schema: str
    claim_digest: str
    evidence_id: str
    evidence_digest: str
    source_identity: str
    field_authority: str
    freshness_ok: bool
    contradiction_state: str
    evaluation_status: str
    qualified: bool
    reasons: tuple[str, ...]


def _claim_digest(record: EvidenceRecord) -> str:
    payload = f"{record.entity.strip().casefold()}|{record.claim.strip().casefold()}"
    return sha256(payload.encode("utf-8")).hexdigest()


def _fresh(record: EvidenceRecord, now: datetime) -> bool:
    if record.freshness_ttl_seconds is None:
        return True
    observed = record.observed_at
    if observed.tzinfo is None:
        observed = observed.replace(tzinfo=timezone.utc)
    return (now - observed).total_seconds() <= record.freshness_ttl_seconds


def create_qualification_receipt(
    record: EvidenceRecord,
    observation: Observation,
    certificate: EvidenceCertificate,
    *,
    field_authority: str,
    authority_allowed: bool,
    evaluation_passed: bool,
    now: datetime | None = None,
) -> EvidenceQualificationReceipt:
    """Bind evidence, source, freshness, contradiction, authority, and evaluation.

    The receipt is deliberately fail-closed. Provenance text or model confidence is
    carried by the underlying evidence record but cannot make an unqualified item
    qualified.
    """
    current = now or datetime.now(timezone.utc)
    certificate_ok = verify_certificate(observation, certificate)
    freshness_ok = _fresh(record, current)
    contradiction_state = "contradictory" if record.result == "contradictory" or record.contradicts else "none"
    evaluation_status = "passed" if evaluation_passed else "failed"
    reasons: list[str] = []

    if record.result != "useful":
        reasons.append(f"evidence result is {record.result}")
    if not certificate_ok:
        reasons.append("evidence certificate verification failed")
    if not freshness_ok:
        reasons.append("evidence is stale")
    if contradiction_state != "none":
        reasons.append("evidence is contradictory")
    if not field_authority.strip():
        reasons.append("field authority is missing")
    if not authority_allowed:
        reasons.append("field authority is not allowed for this claim")
    if not evaluation_passed:
        reasons.append("evaluation did not pass")

    qualified = not reasons
    return EvidenceQualificationReceipt(
        schema="evidence-qualification-receipt/v1",
        claim_digest=_claim_digest(record),
        evidence_id=record.evidence_id,
        evidence_digest=certificate.content_hash,
        source_identity=f"{record.source_family}|{record.source_url}",
        field_authority=field_authority.strip(),
        freshness_ok=freshness_ok,
        contradiction_state=contradiction_state,
        evaluation_status=evaluation_status,
        qualified=qualified,
        reasons=tuple(reasons),
    )
