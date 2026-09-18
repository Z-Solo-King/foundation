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

    def validate(self) -> None:
        if self.max_age is not None and self.max_age.total_seconds() < 0:
            raise ValueError("max_age must not be negative")


@dataclass(frozen=True)
class EvidenceTime:
    observed_at: datetime | None = None
    published_at: datetime | None = None

    def best_timestamp(self) -> datetime | None:
        return self.observed_at or self.published_at


def classify_freshness(
    evidence_time: EvidenceTime,
    requirement: FreshnessRequirement,
    *,
    now: datetime | None = None,
) -> FreshnessState:
    requirement.validate()
    current = now or datetime.now(timezone.utc)
    timestamp = evidence_time.best_timestamp()
    if timestamp is None:
        return FreshnessState.UNKNOWN if requirement.require_timestamp else FreshnessState.FRESH
    if timestamp.tzinfo is None:
        raise ValueError("evidence timestamp must be timezone-aware")
    timestamp = timestamp.astimezone(timezone.utc)
    if timestamp > current:
        return FreshnessState.FUTURE
    if requirement.max_age is None:
        return FreshnessState.FRESH
    return FreshnessState.FRESH if current - timestamp <= requirement.max_age else FreshnessState.STALE
