"""Deterministic temporal evidence/freshness contract."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import StrEnum


FRESHNESS_CONTRACT_VERSION = "temporal-freshness/v1"


class FreshnessState(StrEnum):
    FRESH = "fresh"
    STALE = "stale"
    UNKNOWN = "unknown"
    FUTURE = "future"


class TimestampQuality(StrEnum):
    PRECISE = "precise"
    DATE_ONLY = "date_only"
    INFERRED = "inferred"
    MISSING = "missing"


@dataclass(frozen=True)
class FreshnessRequirement:
    """Request-specific, versioned freshness policy."""

    max_age: timedelta | None = None
    require_timestamp: bool = True
    policy_version: str = FRESHNESS_CONTRACT_VERSION
    historical: bool = False
    allow_future: bool = False
    as_of: datetime | None = None

    def validate(self) -> None:
        if self.max_age is not None and self.max_age.total_seconds() < 0:
            raise ValueError("max_age must not be negative")
        if self.policy_version != FRESHNESS_CONTRACT_VERSION:
            raise ValueError("unsupported freshness policy version")
        if self.as_of is not None and self.as_of.tzinfo is None:
            raise ValueError("as_of must be timezone-aware")


@dataclass(frozen=True)
class EvidenceTime:
    observed_at: datetime | None = None
    published_at: datetime | None = None
    effective_from: datetime | None = None
    effective_to: datetime | None = None
    timestamp_quality: TimestampQuality = TimestampQuality.PRECISE
    revision_id: str | None = None

    def __post_init__(self) -> None:
        for name, value in (
            ("observed_at", self.observed_at),
            ("published_at", self.published_at),
            ("effective_from", self.effective_from),
            ("effective_to", self.effective_to),
        ):
            if value is not None and value.tzinfo is None:
                raise ValueError(f"{name} must be timezone-aware")
        if self.effective_from and self.effective_to and self.effective_to < self.effective_from:
            raise ValueError("effective_to must not precede effective_from")
        if self.timestamp_quality is TimestampQuality.MISSING and (self.observed_at or self.published_at):
            raise ValueError("missing timestamp quality cannot carry timestamps")
        if self.revision_id is not None and not self.revision_id.strip():
            raise ValueError("revision_id must be non-empty when provided")

    def best_timestamp(self) -> datetime | None:
        return self.observed_at or self.published_at


def classify_freshness(
    evidence_time: EvidenceTime,
    requirement: FreshnessRequirement,
    *,
    now: datetime | None = None,
) -> FreshnessState:
    requirement.validate()
    current = requirement.as_of or now or datetime.now(timezone.utc)
    if current.tzinfo is None:
        raise ValueError("now must be timezone-aware")
    current = current.astimezone(timezone.utc)

    if evidence_time.effective_from is not None:
        effective_from = evidence_time.effective_from.astimezone(timezone.utc)
        if current < effective_from:
            return FreshnessState.FUTURE
    if evidence_time.effective_to is not None:
        effective_to = evidence_time.effective_to.astimezone(timezone.utc)
        if current > effective_to:
            return FreshnessState.STALE

    timestamp = evidence_time.best_timestamp()
    if timestamp is None:
        return FreshnessState.UNKNOWN if requirement.require_timestamp else FreshnessState.FRESH

    timestamp = timestamp.astimezone(timezone.utc)
    if timestamp > current and not (requirement.historical or requirement.allow_future):
        return FreshnessState.FUTURE

    if requirement.historical:
        return FreshnessState.FRESH

    if requirement.max_age is None:
        return FreshnessState.FRESH

    age = current - timestamp
    if age < timedelta(0):
        return FreshnessState.FUTURE
    return FreshnessState.FRESH if age <= requirement.max_age else FreshnessState.STALE


def cache_reuse_allowed(
    evidence_time: EvidenceTime,
    requirement: FreshnessRequirement,
    *,
    now: datetime | None = None,
) -> bool:
    """Permit replay/cache reuse only when the current temporal contract is satisfied."""
    return classify_freshness(evidence_time, requirement, now=now) is FreshnessState.FRESH
