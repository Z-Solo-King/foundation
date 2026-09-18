from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class AcquisitionLaneKind(StrEnum):
    STATIC_FETCH = "static_fetch"
    STRUCTURED_DATA = "structured_data"
    SEARCH_DISCOVERY = "search_discovery"
    BROWSER = "browser"


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

    def validate(self) -> None:
        if self.max_attempts < 1:
            raise ValueError("max_attempts must be positive")
        if self.max_cost_units < 1:
            raise ValueError("max_cost_units must be positive")
        if any(not item.strip() for item in self.allowed_capabilities):
            raise ValueError("allowed_capabilities must contain non-empty values")


@dataclass(frozen=True)
class AcquisitionFallbackDecision:
    lane: AcquisitionLane | None
    terminal_reason: AcquisitionOutcome | None
    attempts_remaining: int
    cost_remaining: int


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
    if attempts_used >= policy.max_attempts or cost_used >= policy.max_cost_units:
        return AcquisitionFallbackDecision(None, AcquisitionOutcome.BUDGET_EXHAUSTED, 0, max(0, policy.max_cost_units - cost_used))

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
        return AcquisitionFallbackDecision(
            lane,
            None,
            policy.max_attempts - attempts_used - 1,
            policy.max_cost_units - cost_used - lane.cost_units,
        )
    return AcquisitionFallbackDecision(None, AcquisitionOutcome.BUDGET_EXHAUSTED, 0, max(0, policy.max_cost_units - cost_used))
