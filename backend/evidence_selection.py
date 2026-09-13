"""Public-safe deterministic evidence selection and context-packet primitives.

This module deliberately does not decide private trust policy. Callers provide explicit
source rank and relevance scores; selection only enforces stable budgeting, duplicate
suppression, response reserves and reproducible cache identity.
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


@dataclass(frozen=True)
class ContextPacketBudget:
    total_tokens: int
    answer_reserve_tokens: int = 0
    verification_reserve_tokens: int = 0

    def validate(self) -> None:
        if self.total_tokens < 1:
            raise ValueError("total_tokens must be positive")
        if self.answer_reserve_tokens < 0 or self.verification_reserve_tokens < 0:
            raise ValueError("context reserves must be non-negative")
        if self.answer_reserve_tokens + self.verification_reserve_tokens >= self.total_tokens:
            raise ValueError("context reserves must leave evidence capacity")

    @property
    def evidence_tokens(self) -> int:
        self.validate()
        return self.total_tokens - self.answer_reserve_tokens - self.verification_reserve_tokens


@dataclass(frozen=True)
class ContextPacket:
    selected: tuple[EvidenceCandidate, ...]
    dropped_ids: tuple[str, ...]
    duplicate_count: int
    evidence_tokens: int
    budget: ContextPacketBudget
    content_hash: str
    prefix_cache_key: str

    @property
    def total_budget_used_ratio(self) -> float:
        return self.evidence_tokens / self.budget.evidence_tokens


def estimate_tokens(text: str, *, chars_per_token: int = 4) -> int:
    if chars_per_token < 2:
        raise ValueError("chars_per_token must be at least 2")
    return (len(text) + chars_per_token - 1) // chars_per_token if text else 0


def _dedupe_key(candidate: EvidenceCandidate) -> str:
    normalized = " ".join(candidate.text.casefold().split())
    return sha256(f"{candidate.claim_key}|{normalized}".encode("utf-8")).hexdigest()


def _candidate_tokens(candidate: EvidenceCandidate) -> int:
    return candidate.estimated_tokens if candidate.estimated_tokens is not None else estimate_tokens(candidate.text)


def _packet_hash(selected: tuple[EvidenceCandidate, ...]) -> str:
    canonical = "\n".join(
        f"{item.claim_key}|{item.source_url}|{item.text}" for item in selected
    )
    return sha256(canonical.encode("utf-8")).hexdigest()


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
        estimated = _candidate_tokens(candidate)
        if used_tokens + estimated > max_tokens:
            continue
        selected.append(candidate)
        seen.add(key)
        used_tokens += estimated
        if len(selected) >= max_items:
            break
    return tuple(selected)


def build_context_packet(
    candidates: tuple[EvidenceCandidate, ...],
    *,
    budget: ContextPacketBudget,
    max_items: int,
) -> ContextPacket:
    """Build a reproducible evidence packet with explicit output/verification reserves."""
    budget.validate()
    if max_items < 1:
        raise ValueError("max_items must be positive")
    for candidate in candidates:
        candidate.validate()

    selected = select_evidence(candidates, max_items=max_items, max_tokens=budget.evidence_tokens)
    selected_ids = {item.evidence_id for item in selected}
    seen: set[str] = set()
    duplicate_count = 0
    dropped: list[str] = []
    for candidate in candidates:
        key = _dedupe_key(candidate)
        if key in seen:
            if candidate.evidence_id not in selected_ids:
                duplicate_count += 1
            if candidate.evidence_id not in selected_ids:
                dropped.append(candidate.evidence_id)
            continue
        seen.add(key)
        if candidate.evidence_id not in selected_ids:
            dropped.append(candidate.evidence_id)

    evidence_tokens = sum(_candidate_tokens(item) for item in selected)
    content_hash = _packet_hash(selected)
    prefix_cache_key = sha256(
        ("|".join(item.claim_key for item in selected) + f"|{budget.answer_reserve_tokens}|{budget.verification_reserve_tokens}").encode("utf-8")
    ).hexdigest()
    return ContextPacket(
        selected=selected,
        dropped_ids=tuple(dropped),
        duplicate_count=duplicate_count,
        evidence_tokens=evidence_tokens,
        budget=budget,
        content_hash=content_hash,
        prefix_cache_key=prefix_cache_key,
    )