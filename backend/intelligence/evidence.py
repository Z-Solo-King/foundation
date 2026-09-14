from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from hashlib import sha256
from typing import Literal
from urllib.parse import urlsplit, urlunsplit

ResultKind = Literal["useful", "duplicate", "blocked", "irrelevant", "stale", "contradictory", "failed"]


def canonical_url(value: str) -> str:
    parts = urlsplit(value.strip())
    if parts.scheme.lower() not in {"http", "https"} or not parts.hostname:
        raise ValueError("source URL must be absolute HTTP(S)")
    scheme = parts.scheme.lower()
    host = parts.hostname.lower()
    port = parts.port
    netloc = host if not port or (scheme, port) in {("http", 80), ("https", 443)} else f"{host}:{port}"
    return urlunsplit((scheme, netloc, parts.path or "/", parts.query, ""))


@dataclass(frozen=True)
class EvidenceRecord:
    evidence_id: str
    claim: str
    entity: str
    source_url: str
    source_family: str
    observed_at: datetime
    published_at: datetime | None = None
    result: ResultKind = "useful"
    method: str = "unknown"
    provenance: str = ""
    confidence: float = 0.5
    freshness_ttl_seconds: int | None = None
    revision: str | None = None
    region: str | None = None
    supports: tuple[str, ...] = field(default_factory=tuple)
    contradicts: tuple[str, ...] = field(default_factory=tuple)
    metadata: dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.claim.strip() or not self.entity.strip():
            raise ValueError("claim and entity are required")
        canonical = canonical_url(self.source_url)
        object.__setattr__(self, "source_url", canonical)
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0 and 1")
        if self.freshness_ttl_seconds is not None and self.freshness_ttl_seconds < 0:
            raise ValueError("freshness_ttl_seconds must not be negative")

    @property
    def fingerprint(self) -> str:
        payload = "|".join((self.entity, self.claim.strip().casefold(), self.source_url, self.revision or "", self.region or ""))
        return sha256(payload.encode("utf-8")).hexdigest()


class EvidenceKnowledgeStore:
    """Deterministic in-process evidence store for nightly and chatbot reuse."""

    def __init__(self) -> None:
        self._records: dict[str, EvidenceRecord] = {}

    def add(self, record: EvidenceRecord) -> bool:
        if record.evidence_id in self._records:
            return False
        self._records[record.evidence_id] = record
        return True

    def upsert(self, record: EvidenceRecord) -> None:
        self._records[record.evidence_id] = record

    def get(self, evidence_id: str) -> EvidenceRecord | None:
        return self._records.get(evidence_id)

    def search(self, entity: str, claim_terms: tuple[str, ...] = (), source_family: str | None = None) -> list[EvidenceRecord]:
        entity_key = entity.casefold()
        terms = tuple(term.casefold() for term in claim_terms if term.strip())
        rows = []
        for record in self._records.values():
            if record.entity.casefold() != entity_key:
                continue
            if source_family and record.source_family != source_family:
                continue
            if terms and not all(term in record.claim.casefold() for term in terms):
                continue
            rows.append(record)
        return sorted(rows, key=lambda row: (row.confidence, row.observed_at), reverse=True)

    def is_fresh(self, record: EvidenceRecord, now: datetime | None = None) -> bool:
        if record.freshness_ttl_seconds is None:
            return True
        current = now or datetime.now(timezone.utc)
        observed = record.observed_at
        if observed.tzinfo is None:
            observed = observed.replace(tzinfo=timezone.utc)
        return (current - observed).total_seconds() <= record.freshness_ttl_seconds

    def reusable(self, entity: str, claim_terms: tuple[str, ...] = (), now: datetime | None = None) -> list[EvidenceRecord]:
        return [row for row in self.search(entity, claim_terms) if row.result == "useful" and self.is_fresh(row, now)]

    def stale(self, entity: str, claim_terms: tuple[str, ...] = (), now: datetime | None = None) -> list[EvidenceRecord]:
        return [row for row in self.search(entity, claim_terms) if not self.is_fresh(row, now)]

    def contradictions(self, entity: str, claim_terms: tuple[str, ...] = ()) -> list[EvidenceRecord]:
        return [row for row in self.search(entity, claim_terms) if row.contradicts or row.result == "contradictory"]

    def export(self) -> list[dict[str, object]]:
        return [
            {
                "evidence_id": row.evidence_id,
                "claim": row.claim,
                "entity": row.entity,
                "source_url": row.source_url,
                "source_family": row.source_family,
                "observed_at": row.observed_at.isoformat(),
                "published_at": row.published_at.isoformat() if row.published_at else None,
                "result": row.result,
                "method": row.method,
                "provenance": row.provenance,
                "confidence": row.confidence,
                "freshness_ttl_seconds": row.freshness_ttl_seconds,
                "revision": row.revision,
                "region": row.region,
                "supports": list(row.supports),
                "contradicts": list(row.contradicts),
                "metadata": dict(row.metadata),
            }
            for row in self._records.values()
        ]
