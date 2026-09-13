"""Deterministic external-service limit observations and route activation guards.

A service limit is usable only when it was explicitly observed and is fresh enough for the
caller. Unknown limits remain unknown; this module never invents free quota or billing state.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class LimitConfidence(StrEnum):
    VERIFIED = "verified"
    STALE = "stale"
    UNKNOWN = "unknown"
    CONTRADICTORY = "contradictory"


@dataclass(frozen=True)
class ServiceLimitObservation:
    service_id: str
    resource: str
    observed_at: float
    available_units: int | None
    reset_at: float | None = None
    source: str = ""
    observation_id: str = ""
    confidence: LimitConfidence = LimitConfidence.VERIFIED

    def validate(self) -> None:
        for name in ("service_id", "resource", "source", "observation_id"):
            if not isinstance(getattr(self, name), str) or not getattr(self, name).strip():
                raise ValueError(f"{name} must not be empty")
        if self.observed_at < 0:
            raise ValueError("observed_at must be non-negative")
        if self.available_units is not None and self.available_units < 0:
            raise ValueError("available_units must be non-negative")
        if self.reset_at is not None and self.reset_at < 0:
            raise ValueError("reset_at must be non-negative")
        if self.reset_at is not None and self.reset_at < self.observed_at:
            raise ValueError("reset_at must not precede observed_at")
        if not isinstance(self.confidence, LimitConfidence):
            raise ValueError("confidence must be a LimitConfidence")

    def is_fresh(self, now: float, max_age_seconds: float) -> bool:
        self.validate()
        if now < 0 or max_age_seconds < 0:
            raise ValueError("time and age bounds must be non-negative")
        return self.confidence is LimitConfidence.VERIFIED and now - self.observed_at <= max_age_seconds


@dataclass(frozen=True)
class RouteActivationGuard:
    service_id: str
    resource: str
    required_units: int = 1
    max_limit_age_seconds: float = 300.0

    def validate(self) -> None:
        if not self.service_id.strip() or not self.resource.strip():
            raise ValueError("route guard identity must not be empty")
        if self.required_units < 1:
            raise ValueError("required_units must be positive")
        if self.max_limit_age_seconds < 0:
            raise ValueError("max_limit_age_seconds must be non-negative")


def route_activation_allowed(
    guard: RouteActivationGuard,
    observation: ServiceLimitObservation | None,
    *,
    now: float,
) -> bool:
    """Allow activation only from a fresh verified limit observation with capacity."""
    guard.validate()
    if now < 0:
        return False
    if observation is None:
        return False
    observation.validate()
    if observation.service_id != guard.service_id or observation.resource != guard.resource:
        return False
    if not observation.is_fresh(now, guard.max_limit_age_seconds):
        return False
    if observation.available_units is None:
        return False
    return observation.available_units >= guard.required_units


def reconcile_limit(previous: ServiceLimitObservation | None, current: ServiceLimitObservation) -> ServiceLimitObservation:
    """Mark contradictory independent limit observations explicitly instead of picking one."""
    current.validate()
    if previous is None:
        return current
    previous.validate()
    if previous.service_id != current.service_id or previous.resource != current.resource:
        raise ValueError("cannot reconcile different service resources")
    if previous.available_units is not None and current.available_units is not None:
        if previous.available_units != current.available_units and previous.observed_at == current.observed_at:
            return ServiceLimitObservation(
                current.service_id,
                current.resource,
                current.observed_at,
                current.available_units,
                current.reset_at,
                current.source,
                current.observation_id,
                LimitConfidence.CONTRADICTORY,
            )
    return current


__all__ = [
    "LimitConfidence",
    "ServiceLimitObservation",
    "RouteActivationGuard",
    "route_activation_allowed",
    "reconcile_limit",
]