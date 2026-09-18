from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


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
    version: str = ADMISSION_CONTRACT_VERSION
    window_seconds: int = 60
    max_requests_per_subject: int = 30
    max_requests_global: int = 300
    max_concurrent_per_subject: int = 2
    max_concurrent_global: int = 20
    retry_after_seconds: int = 5
    protected_routes: tuple[AdmissionRoute, ...] = (AdmissionRoute.CHAT, AdmissionRoute.RESEARCH, AdmissionRoute.STREAM)

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


@dataclass(frozen=True)
class AdmissionSnapshot:
    authority_available: bool
    subject_requests: int = 0
    global_requests: int = 0
    subject_concurrent: int = 0
    global_concurrent: int = 0

    def validate(self) -> None:
        values = (
            self.subject_requests,
            self.global_requests,
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
