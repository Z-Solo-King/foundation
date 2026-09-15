"""Research-memory scaffold; not currently wired into the live execution path.

This module is retained as a validated planning primitive for future durable
research-memory integration. It must not be treated as a second memory or
persistence authority while the active pipeline remains elsewhere.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Literal

from .evidence import EvidenceKnowledgeStore, EvidenceRecord, canonical_url

VisitResult = Literal["useful", "duplicate", "blocked", "irrelevant", "stale", "contradictory", "failed"]


@dataclass(frozen=True)
class SourceVisit:
    task_id: str
    url: str
    source_family: str
    purpose: str
    method: str
    result: VisitResult
    visited_at: datetime
    finding: str = ""
    revisit_after: datetime | None = None
    revisit_reason: str | None = None

    def __post_init__(self) -> None:
        if not self.task_id.strip() or not self.source_family.strip() or not self.purpose.strip():
            raise ValueError("task_id, source_family and purpose are required")
        object.__setattr__(self, "url", canonical_url(self.url))

    @property
    def dedupe_key(self) -> str:
        return f"{self.task_id}|{self.url}"

    def reusable(self, now: datetime | None = None) -> bool:
        if self.result != "useful":
            return False
        if self.revisit_after is None:
            return True
        current = now or datetime.now(timezone.utc)
        return current < self.revisit_after


@dataclass
class ResearchMemory:
    """Shared persisted memory for nightly research and future chatbot questions."""

    visits: dict[str, SourceVisit] = field(default_factory=dict)
    evidence: EvidenceKnowledgeStore = field(default_factory=EvidenceKnowledgeStore)

    def record_visit(self, visit: SourceVisit) -> bool:
        key = visit.dedupe_key
        if key in self.visits:
            return False
        self.visits[key] = visit
        return True

    def should_visit(self, task_id: str, url: str, now: datetime | None = None) -> bool:
        key = f"{task_id}|{canonical_url(url)}"
        previous = self.visits.get(key)
        return previous is None or not previous.reusable(now)

    def prior_visits(self, task_id: str) -> list[SourceVisit]:
        return sorted((row for row in self.visits.values() if row.task_id == task_id), key=lambda row: row.visited_at)

    def unseen_domains(self, task_id: str, candidate_urls: list[str]) -> list[str]:
        visited_hosts = {url.split("/", 3)[2].casefold() for url in (row.url for row in self.prior_visits(task_id))}
        fresh: list[str] = []
        for value in candidate_urls:
            url = canonical_url(value)
            host = url.split("/", 3)[2].casefold()
            if host not in visited_hosts and url not in fresh:
                fresh.append(url)
        return fresh

    def add_evidence(self, record: EvidenceRecord) -> bool:
        return self.evidence.add(record)

    def reusable_evidence(self, entity: str, claim_terms: tuple[str, ...] = (), now: datetime | None = None) -> list[EvidenceRecord]:
        return self.evidence.reusable(entity, claim_terms, now)

    def to_json(self) -> str:
        payload = {
            "schema": "research-memory/v1",
            "visits": [
                {
                    "task_id": row.task_id,
                    "url": row.url,
                    "source_family": row.source_family,
                    "purpose": row.purpose,
                    "method": row.method,
                    "result": row.result,
                    "visited_at": row.visited_at.isoformat(),
                    "finding": row.finding,
                    "revisit_after": row.revisit_after.isoformat() if row.revisit_after else None,
                    "revisit_reason": row.revisit_reason,
                }
                for row in self.visits.values()
            ],
            "evidence": self.evidence.export(),
        }
        return json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True)

    @classmethod
    def from_json(cls, payload: str) -> "ResearchMemory":
        value = json.loads(payload)
        if value.get("schema") != "research-memory/v1":
            raise ValueError("unsupported research memory schema")
        memory = cls()
        for item in value.get("visits", []):
            visit = SourceVisit(
                task_id=str(item["task_id"]),
                url=str(item["url"]),
                source_family=str(item["source_family"]),
                purpose=str(item["purpose"]),
                method=str(item["method"]),
                result=str(item["result"]),
                visited_at=datetime.fromisoformat(str(item["visited_at"])),
                finding=str(item.get("finding") or ""),
                revisit_after=datetime.fromisoformat(str(item["revisit_after"])) if item.get("revisit_after") else None,
                revisit_reason=str(item["revisit_reason"]) if item.get("revisit_reason") else None,
            )
            memory.visits[visit.dedupe_key] = visit
        for item in value.get("evidence", []):
            record = EvidenceRecord(
                evidence_id=str(item["evidence_id"]),
                claim=str(item["claim"]),
                entity=str(item["entity"]),
                source_url=str(item["source_url"]),
                source_family=str(item["source_family"]),
                observed_at=datetime.fromisoformat(str(item["observed_at"])),
                published_at=datetime.fromisoformat(str(item["published_at"])) if item.get("published_at") else None,
                result=str(item.get("result", "useful")),
                method=str(item.get("method", "unknown")),
                provenance=str(item.get("provenance", "")),
                confidence=float(item.get("confidence", 0.5)),
                freshness_ttl_seconds=item.get("freshness_ttl_seconds"),
                revision=item.get("revision"),
                region=item.get("region"),
                supports=tuple(item.get("supports", [])),
                contradicts=tuple(item.get("contradicts", [])),
                metadata=dict(item.get("metadata", {})),
            )
            memory.evidence.upsert(record)
        return memory
