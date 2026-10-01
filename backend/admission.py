from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Mapping


ADMISSION_CONTRACT_VERSION = "public-admission/v1"


class AdmissionRoute(StrEnum):
    CHEAP_READ = "cheap_read"
    CHAT = "chat"
    RESEARCH = "research"
    STREAM = "stream"


class AdmissionOutcome(StrEnum):
    ACCEPTED = "accepted"
    RATE_LIMITED = "rate_limited"
    CONCURRENCY_LIMITED = "concurrency_limited"
    DUPLICATE = "duplicate"
    AUTHORITY_UNAVAILABLE = "authority_unavailable"


@dataclass(frozen=True)
class AdmissionPolicy:
    """Public contract for an admission policy supplied by the private authority."""
    version: str
    window_seconds: int
    max_requests_per_subject: int
    max_requests_global: int
    max_concurrent_per_subject: int
    max_concurrent_global: int
    retry_after_seconds: int
    protected_routes: tuple[AdmissionRoute, ...]

    @classmethod
    def from_mapping(cls, payload: Mapping[str, object]) -> "AdmissionPolicy":
        try:
            return cls(
                version=str(payload["version"]),
                window_seconds=int(payload["window_seconds"]),
                max_requests_per_subject=int(payload["max_requests_per_subject"]),
                max_requests_global=int(payload["max_requests_global"]),
                max_concurrent_per_subject=int(payload["max_concurrent_per_subject"]),
                max_concurrent_global=int(payload["max_concurrent_global"]),
                retry_after_seconds=int(payload["retry_after_seconds"]),
                protected_routes=tuple(AdmissionRoute(str(x)) for x in payload["protected_routes"]),
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError("invalid private admission policy envelope") from exc

    def validate(self) -> None:
        if self.version != ADMISSION_CONTRACT_VERSION:
            raise ValueError("unsupported admission contract version")
        values = (
            self.window_seconds,
            self.max_requests_per_subject,
            self.max_requests_global,
            self.max_concurrent_per_subject,
            self.max_concurrent_global,
            self.retry_after_seconds,
        )
        if any(value < 1 for value in values):
            raise ValueError("admission limits must be positive")
        if not self.protected_routes:
            raise ValueError("protected_routes must not be empty")


@dataclass(frozen=True)
class AdmissionSnapshot:
    authority_available: bool
    subject_requests: int = 0
    global_requests: int = 0
    subject_cost_units: int = 0
    global_cost_units: int = 0
    subject_concurrent: int = 0
    global_concurrent: int = 0

    def validate(self) -> None:
        values = (
            self.subject_requests,
            self.global_requests,
            self.subject_cost_units,
            self.global_cost_units,
            self.subject_concurrent,
            self.global_concurrent,
        )
        if any(value < 0 for value in values):
            raise ValueError("admission counters must be non-negative")


@dataclass(frozen=True)
class AdmissionDecision:
    outcome: AdmissionOutcome
    route: AdmissionRoute
    allowed: bool
    reason: str
    retry_after_seconds: int = 0
    contract_version: str = ADMISSION_CONTRACT_VERSION

    @property
    def retry_after_header(self) -> str | None:
        return str(self.retry_after_seconds) if self.retry_after_seconds > 0 else None


def _admission_limit_decision(policy: AdmissionPolicy, snapshot: AdmissionSnapshot, route: AdmissionRoute) -> AdmissionDecision | None:
    checks = (
        (snapshot.global_requests >= policy.max_requests_global, AdmissionOutcome.RATE_LIMITED, "global admission request ceiling reached"),
        (snapshot.subject_requests >= policy.max_requests_per_subject, AdmissionOutcome.RATE_LIMITED, "subject admission request ceiling reached"),
        (snapshot.global_cost_units >= policy.max_requests_global, AdmissionOutcome.RATE_LIMITED, "global admission cost ceiling reached"),
        (snapshot.subject_cost_units >= policy.max_requests_per_subject, AdmissionOutcome.RATE_LIMITED, "subject admission cost ceiling reached"),
        (snapshot.global_concurrent >= policy.max_concurrent_global, AdmissionOutcome.CONCURRENCY_LIMITED, "global admission concurrency ceiling reached"),
        (snapshot.subject_concurrent >= policy.max_concurrent_per_subject, AdmissionOutcome.CONCURRENCY_LIMITED, "subject admission concurrency ceiling reached"),
    )
    for exceeded, outcome, reason in checks:
        if exceeded:
            return AdmissionDecision(outcome, route, False, reason, policy.retry_after_seconds)
    return None


def decide_admission(
    *,
    policy: AdmissionPolicy,
    snapshot: AdmissionSnapshot,
    subject_fingerprint: str,
    route: AdmissionRoute,
    duplicate: bool = False,
) -> AdmissionDecision:
    policy.validate()
    snapshot.validate()
    if not subject_fingerprint.strip():
        raise ValueError("subject_fingerprint is required")
    if duplicate:
        return AdmissionDecision(
            AdmissionOutcome.DUPLICATE,
            route,
            False,
            "duplicate request is suppressed by the existing idempotency authority",
        )
    if not snapshot.authority_available:
        allowed = route not in policy.protected_routes
        return AdmissionDecision(
            AdmissionOutcome.ACCEPTED if allowed else AdmissionOutcome.AUTHORITY_UNAVAILABLE,
            route,
            allowed,
            "admission authority is unavailable but route is unprotected"
            if allowed else "admission authority is unavailable for a protected route",
            0 if allowed else policy.retry_after_seconds,
        )
    return _admission_limit_decision(policy, snapshot, route) or AdmissionDecision(
        AdmissionOutcome.ACCEPTED,
        route,
        True,
        "admission accepted; authoritative resource spend remains elsewhere",
    )
