"""Public-safe deterministic evidence selection primitives.

This module deliberately does not decide private trust policy. Callers provide an explicit
source rank and relevance score; the selector only enforces stable budgeting and duplicate
suppression so downstream AI systems receive dense evidence rather than repeated prose.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256


@dataclass(frozen=True)
class EvidenceCandidate:
    evidence_id: str
    claim_key: str
    text: str
    source_url: str
    source_rank: int = 0
    relevance_score: int = 0
    estimated_tokens: int | None = None

    def validate(self) -> None:
        if not self.evidence_id.strip():
            raise ValueError("evidence_id must not be empty")
        if not self.claim_key.strip():
            raise ValueError("claim_key must not be empty")
        if not self.source_url.strip():
            raise ValueError("source_url must not be empty")
        if self.source_rank < 0 or self.relevance_score < 0:
            raise ValueError("evidence scores must be non-negative")
        if self.estimated_tokens is not None and self.estimated_tokens < 0:
            raise ValueError("estimated_tokens must not be negative")


def estimate_tokens(text: str, *, chars_per_token: int = 4) -> int:
    if chars_per_token < 2:
        raise ValueError("chars_per_token must be at least 2")
    return (len(text) + chars_per_token - 1) // chars_per_token if text else 0


def _dedupe_key(candidate: EvidenceCandidate) -> str:
    normalized = " ".join(candidate.text.casefold().split())
    return sha256(f"{candidate.claim_key}|{normalized}".encode("utf-8")).hexdigest()


def select_evidence(
    candidates: tuple[EvidenceCandidate, ...],
    *,
    max_items: int,
    max_tokens: int,
) -> tuple[EvidenceCandidate, ...]:
    """Return stable, deduplicated evidence within a deterministic budget."""
    if max_items < 1 or max_tokens < 1:
        raise ValueError("evidence budgets must be positive")
    for candidate in candidates:
        candidate.validate()

    ranked = sorted(
        candidates,
        key=lambda item: (-item.source_rank, -item.relevance_score, item.claim_key, item.evidence_id),
    )
    selected: list[EvidenceCandidate] = []
    seen: set[str] = set()
    used_tokens = 0
    for candidate in ranked:
        key = _dedupe_key(candidate)
        if key in seen:
            continue
        estimated = candidate.estimated_tokens if candidate.estimated_tokens is not None else estimate_tokens(candidate.text)
        if used_tokens + estimated > max_tokens:
            continue
        selected.append(candidate)
        seen.add(key)
        used_tokens += estimated
        if len(selected) >= max_items:
            break
    return tuple(selected)
