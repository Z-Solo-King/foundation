"""Deterministic negative route memory: cooldown, quarantine and recovery state."""
from __future__ import annotations

from dataclasses import dataclass, replace
from enum import Enum
from typing import Mapping, Sequence

from .planner_models import FailureClass, MethodCandidate


class RouteDisposition(Enum):
    ELIGIBLE = "eligible"
    COOLDOWN = "cooldown"
    QUARANTINED = "quarantined"
    RECOVERING = "recovering"


@dataclass(frozen=True)
class RouteKey:
    source_id: str
    method_id: str
    representation: str


@dataclass(frozen=True)
class RouteState:
    attempts: int = 0
    successes: int = 0
    consecutive_failures: int = 0
    last_success_at: float | None = None
    last_failure_at: float | None = None
    cooldown_until: float | None = None
    quarantined_until: float | None = None
    last_failure: FailureClass | None = None
    version: int = 0

    @property
    def success_rate(self) -> float:
        if self.attempts <= 0:
            return 0.0
        return self.successes / self.attempts


def _clamp_time(value: float) -> float:
    if value < 0:
        raise ValueError("route timestamps must be non-negative")
    return value


def _retryable_failure(failure: FailureClass | None) -> bool:
    return failure in {
        FailureClass.TRANSPORT,
        FailureClass.TIMEOUT,
        FailureClass.RATE_LIMITED,
        FailureClass.RATE_LIMIT,
        FailureClass.PARTIAL,
        FailureClass.LOW_YIELD,
        FailureClass.QUOTA,
    }


def _quarantine_failure(failure: FailureClass | None) -> bool:
    return failure in {
        FailureClass.AUTH,
        FailureClass.AUTH_REQUIRED,
        FailureClass.FORBIDDEN,
        FailureClass.POLICY,
        FailureClass.CAPTCHA,
    }


def cooldown_seconds(state: RouteState, failure: FailureClass | None, base: float = 15.0, cap: float = 900.0) -> float:
    if base <= 0 or cap <= 0 or base > cap:
        raise ValueError("cooldown bounds are invalid")
    if not _retryable_failure(failure):
        return 0.0
    exponent = max(0, min(8, state.consecutive_failures - 1))
    return min(cap, base * (2**exponent))


def disposition(state: RouteState, now: float) -> RouteDisposition:
    now = _clamp_time(now)
    if state.quarantined_until is not None and now < state.quarantined_until:
        return RouteDisposition.QUARANTINED
    if state.cooldown_until is not None and now < state.cooldown_until:
        return RouteDisposition.COOLDOWN
    if state.consecutive_failures > 0:
        return RouteDisposition.RECOVERING
    return RouteDisposition.ELIGIBLE


def eligible(state: RouteState, now: float) -> bool:
    return disposition(state, now) in {RouteDisposition.ELIGIBLE, RouteDisposition.RECOVERING}


def apply_route_memory(
    methods: Sequence[MethodCandidate],
    memory: Mapping[RouteKey, RouteState] | None,
    now: float,
) -> tuple[MethodCandidate, ...]:
    """Filter empirically blocked routes without becoming a policy authority."""
    if not memory:
        return tuple(methods)
    kept: list[MethodCandidate] = []
    for method in methods:
        key = RouteKey(method.source_id, method.method_id, method.representation)
        state = memory.get(key)
        if state is None or eligible(state, now):
            kept.append(method)
    return tuple(kept)


def record_failure(
    state: RouteState,
    failure: FailureClass,
    now: float,
    quarantine_after: int = 3,
    quarantine_seconds: float = 3600.0,
) -> RouteState:
    now = _clamp_time(now)
    if quarantine_after < 1 or quarantine_seconds <= 0:
        raise ValueError("quarantine thresholds are invalid")
    attempts = state.attempts + 1
    consecutive = state.consecutive_failures + 1
    cooldown = now + cooldown_seconds(state, failure)
    quarantine = state.quarantined_until
    if _quarantine_failure(failure) or consecutive >= quarantine_after:
        quarantine = now + quarantine_seconds
    return replace(
        state,
        attempts=attempts,
        consecutive_failures=consecutive,
        last_failure_at=now,
        last_failure=failure,
        cooldown_until=cooldown if cooldown > now else state.cooldown_until,
        quarantined_until=quarantine,
        version=state.version + 1,
    )


def record_success(state: RouteState, now: float) -> RouteState:
    now = _clamp_time(now)
    return replace(
        state,
        attempts=state.attempts + 1,
        successes=state.successes + 1,
        consecutive_failures=0,
        last_success_at=now,
        cooldown_until=None,
        quarantined_until=None,
        last_failure=None,
        version=state.version + 1,
    )


def recover(state: RouteState, now: float) -> RouteState:
    now = _clamp_time(now)
    if state.quarantined_until is not None and now < state.quarantined_until:
        return state
    return replace(state, cooldown_until=None, quarantined_until=None, consecutive_failures=0, version=state.version + 1)


def update_memory(memory: Mapping[RouteKey, RouteState], key: RouteKey, state: RouteState) -> dict[RouteKey, RouteState]:
    if not key.source_id or not key.method_id or not key.representation:
        raise ValueError("route identity must be non-empty")
    updated = dict(memory)
    updated[key] = state
    return updated


__all__ = [
    "RouteDisposition",
    "RouteKey",
    "RouteState",
    "cooldown_seconds",
    "disposition",
    "eligible",
    "apply_route_memory",
    "record_failure",
    "record_success",
    "recover",
    "update_memory",
]