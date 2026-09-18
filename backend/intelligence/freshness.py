"""Deterministic temporal evidence/freshness contract."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import StrEnum


class FreshnessState(StrEnum):
    FRESH = "fresh"
    STALE = "stale"
    UNKNOWN = "unknown"
    FUTURE = "future"


@dataclass(frozen=True)
class FreshnessRequirement:
    """Request-specific freshness policy."""

    max_age: timedelta | None = None
    require_timestamp: bool = True
    allow_historical: bool = False

    def validate(self) -> None:
        if self.max_age is not None and self.max_age.total_seconds() < 0:
            raise ValueError("max_age must not be negative")


@dataclass(frozen=True)
class EvidenceTime:
    observed_at: datetime | None = None
    published_at: datetime | None = None
    effective_from: datetime | None = None
    effective_to: datetime | None = None

    def best_timestamp(self) -> datetime | None:
        return self.observed_at or self.published_at

    def validate(self) -> None:
        values = [value for value in (self.observed_at, self.published_at, self.effective_from, self.effective_to) if value is not None]
        if any(value.tzinfo is None for value in values):
            raise ValueError("evidence timestamp must be timezone-aware")
        if self.effective_from and self.effective_to and self.effective_to < self.effective_from:
            raise ValueError("effective_to must not precede effective_from")


def classify_freshness(
    evidence_time: EvidenceTime,
    requirement: FreshnessRequirement,
    *,
    now: datetime | None = None,
) -> FreshnessState:
    requirement.validate()
    evidence_time.validate()
    current = now or datetime.now(timezone.utc)
    if current.tzinfo is None:
        raise ValueError("now must be timezone-aware")
    current = current.astimezone(timezone.utc)
    if evidence_time.effective_from and current < evidence_time.effective_from.astimezone(timezone.utc):
        return FreshnessState.FUTURE
    if evidence_time.effective_to and current > evidence_time.effective_to.astimezone(timezone.utc):
        return FreshnessState.STALE
    timestamp = evidence_time.best_timestamp()
    if timestamp is None:
        return FreshnessState.UNKNOWN if requirement.require_timestamp else FreshnessState.FRESH
    timestamp = timestamp.astimezone(timezone.utc)
    if timestamp > current:
        return FreshnessState.FUTURE
    if requirement.max_age is None:
        return FreshnessState.FRESH
    return FreshnessState.FRESH if current - timestamp <= requirement.max_age else FreshnessState.STALE


def cache_replay_allowed(state: FreshnessState, *, requirement: FreshnessRequirement) -> bool:
    requirement.validate()
    return state is FreshnessState.FRESH or (state is FreshnessState.UNKNOWN and not requirement.require_timestamp)
