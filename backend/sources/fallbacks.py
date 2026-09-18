from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
import hashlib
import json


class AcquisitionLaneKind(StrEnum):
    STATIC_FETCH = "static_fetch"
    STRUCTURED_DATA = "structured_data"
    SEARCH_DISCOVERY = "search_discovery"
    BROWSER = "browser"


class AcquisitionDecisionCode(StrEnum):
    READY = "ready"
    ATTEMPTS_EXHAUSTED = "attempts_exhausted"
    COST_EXHAUSTED = "cost_exhausted"
    NO_AUTHORIZED_LANE = "no_authorized_lane"
    NO_BUDGET_FIT = "no_budget_fit"


class AcquisitionOutcome(StrEnum):
    SUCCESS = "success"
    TRANSPORT_FAILURE = "transport_failure"
    CHALLENGE = "challenge"
    TIMEOUT = "timeout"
    NOT_FOUND = "not_found"
    DUPLICATE = "duplicate"
    BUDGET_EXHAUSTED = "budget_exhausted"


@dataclass(frozen=True)
class AcquisitionLane:
    name: str
    kind: AcquisitionLaneKind
    capability: str
    cost_units: int
    requires_browser: bool = False
    evidence_capable: bool = True
    authorized: bool = True
    priority: int = 0

    def validate(self) -> None:
        if not self.name.strip() or not self.capability.strip():
            raise ValueError("lane name and capability are required")
        if self.cost_units < 1:
            raise ValueError("lane cost_units must be positive")
        if self.requires_browser and self.kind is not AcquisitionLaneKind.BROWSER:
            raise ValueError("browser-required lanes must use the browser lane kind")


@dataclass(frozen=True)
class AcquisitionFallbackPolicy:
    max_attempts: int = 3
    max_cost_units: int = 6
    allow_browser: bool = False
    allowed_capabilities: tuple[str, ...] = ()
    revision: str = "acquisition-fallback/v1"

    def validate(self) -> None:
        if self.max_attempts < 1:
            raise ValueError("max_attempts must be positive")
        if self.max_cost_units < 1:
            raise ValueError("max_cost_units must be positive")
        if any(not item.strip() for item in self.allowed_capabilities):
            raise ValueError("allowed_capabilities must contain non-empty values")
        if not self.revision.strip():
            raise ValueError("revision must be non-empty")


@dataclass(frozen=True)
class AcquisitionFallbackDecision:
    lane: AcquisitionLane | None
    terminal_reason: AcquisitionOutcome | None
    attempts_remaining: int
    cost_remaining: int
    decision_code: AcquisitionDecisionCode = AcquisitionDecisionCode.READY
    policy_revision: str = ""
    digest: str = ""

    def to_dict(self) -> dict[str, object]:
        return {
            "schema": "acquisition-fallback-decision/v1",
            "lane": self.lane.name if self.lane else None,
            "terminal_reason": self.terminal_reason.value if self.terminal_reason else None,
            "attempts_remaining": self.attempts_remaining,
            "cost_remaining": self.cost_remaining,
            "decision_code": self.decision_code.value,
            "policy_revision": self.policy_revision,
            "digest": self.digest,
        }


DEFAULT_ACQUISITION_LANES = (
    AcquisitionLane("static_fetch", AcquisitionLaneKind.STATIC_FETCH, "static_http", 1, priority=10),
    AcquisitionLane("structured_data", AcquisitionLaneKind.STRUCTURED_DATA, "structured_data", 1, priority=20),
    AcquisitionLane(
        "search_discovery",
        AcquisitionLaneKind.SEARCH_DISCOVERY,
        "search",
        2,
        evidence_capable=False,
        priority=30,
    ),
    AcquisitionLane(
        "browser",
        AcquisitionLaneKind.BROWSER,
        "browser",
        5,
        requires_browser=True,
        priority=40,
    ),
)


def choose_next_lane(
    *,
    policy: AcquisitionFallbackPolicy,
    failed_lanes: tuple[str, ...] = (),
    attempts_used: int = 0,
    cost_used: int = 0,
    lanes: tuple[AcquisitionLane, ...] = DEFAULT_ACQUISITION_LANES,
) -> AcquisitionFallbackDecision:
    policy.validate()
    if attempts_used < 0 or cost_used < 0:
        raise ValueError("attempts_used and cost_used must be non-negative")
    def build(lane, terminal_reason, attempts_remaining, cost_remaining, decision_code):
        payload = {
            "lane": lane.name if lane else None,
            "terminal_reason": terminal_reason.value if terminal_reason else None,
            "attempts_remaining": attempts_remaining,
            "cost_remaining": cost_remaining,
            "decision_code": decision_code.value,
            "policy_revision": policy.revision,
        }
        digest = hashlib.sha256(
            json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()
        return AcquisitionFallbackDecision(
            lane,
            terminal_reason,
            attempts_remaining,
            cost_remaining,
            decision_code,
            policy.revision,
            digest,
        )

    if attempts_used >= policy.max_attempts:
        return build(None, AcquisitionOutcome.BUDGET_EXHAUSTED, 0, max(0, policy.max_cost_units - cost_used), AcquisitionDecisionCode.ATTEMPTS_EXHAUSTED)
    if cost_used >= policy.max_cost_units:
        return build(None, AcquisitionOutcome.BUDGET_EXHAUSTED, max(0, policy.max_attempts - attempts_used), 0, AcquisitionDecisionCode.COST_EXHAUSTED)

    failed = set(failed_lanes)
    for lane in sorted(lanes, key=lambda item: (item.priority, item.name)):
        lane.validate()
        if lane.name in failed or not lane.authorized:
            continue
        if lane.requires_browser and not policy.allow_browser:
            continue
        if policy.allowed_capabilities and lane.capability not in policy.allowed_capabilities:
            continue
        if cost_used + lane.cost_units > policy.max_cost_units:
            continue
        return build(
            lane,
            None,
            policy.max_attempts - attempts_used - 1,
            policy.max_cost_units - cost_used - lane.cost_units,
            AcquisitionDecisionCode.READY,
        )
    decision_code = (
        AcquisitionDecisionCode.NO_AUTHORIZED_LANE
        if any(item.authorized and not (item.requires_browser and not policy.allow_browser) for item in lanes)
        else AcquisitionDecisionCode.NO_BUDGET_FIT
    )
    return build(
        None,
        AcquisitionOutcome.BUDGET_EXHAUSTED,
        max(0, policy.max_attempts - attempts_used),
        max(0, policy.max_cost_units - cost_used),
        decision_code,
    )
