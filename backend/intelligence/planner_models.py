"""Typed, immutable planner models used by the canonical research planner.

The planner owns decision metadata; it does not perform network I/O or enforce
protected policy. Policy/resource authorities remain separate consumers.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Mapping, Sequence


class TaskMode(str, Enum):
    FACT = "fact"
    SPECIFICATION = "specification"
    COMPARISON = "comparison"
    RECOMMENDATION = "recommendation"
    PRICE_AVAILABILITY = "price_availability"
    DIAGNOSIS = "diagnosis"
    TEMPORAL = "temporal"
    CONTRADICTION = "contradiction"
    COMMUNITY = "community"
    PRIMARY_SOURCE = "primary_source"
    ENTITY_RESOLUTION = "entity_resolution"
    DOCUMENT = "document"
    CODE = "code"
    DATA = "data"
    MEDIA = "media"
    MIXED = "mixed"


class FactType(str, Enum):
    IDENTITY = "identity"
    AVAILABILITY = "availability"
    COMMERCIAL = "commercial"
    SPECIFICATION = "specification"
    CONFIGURATION = "configuration"
    TEMPORAL = "temporal"
    QUALITATIVE = "qualitative"
    NORMATIVE = "normative"
    RELATIONAL = "relational"
    DERIVED = "derived"


class CoverageState(str, Enum):
    SATISFIED = "satisfied"
    PARTIAL = "partial"
    UNSUPPORTED = "unsupported"
    CONTRADICTED = "contradicted"
    STALE = "stale"
    INACCESSIBLE = "inaccessible"
    BLOCKED = "blocked"
    AMBIGUOUS = "ambiguous"
    DERIVED_ONLY = "derived_only"


class FailureClass(str, Enum):
    EMPTY = "empty"
    NOT_FOUND = "404"
    FORBIDDEN = "403"
    RATE_LIMITED = "429"
    SERVER_ERROR = "5xx"
    CAPTCHA = "captcha_challenge"
    AUTH_REQUIRED = "auth_required"
    PARSER = "parser_failure"
    MALFORMED = "malformed_payload"
    TRANSPORT = "transport_error"
    ENCODING = "encoding_error"
    PARTIAL = "partial_response"
    UNKNOWN = "unknown_failure"


class StopReason(str, Enum):
    QUALITY_FLOOR = "quality_floor_met"
    LOW_INFORMATION_GAIN = "low_information_gain"
    BUDGET_EXHAUSTED = "budget_exhausted"
    WALL_TIME = "wall_time_exhausted"
    POLICY_BLOCKED = "policy_blocked"
    CAPABILITY_MISSING = "capability_missing"
    UNRESOLVED_CONTRADICTION = "unresolved_contradiction"
    USER_LIMIT = "user_limit"
    FAILED = "failed"


@dataclass(frozen=True)
class ClaimRequirement:
    claim_id: str
    text: str
    fact_type: FactType = FactType.IDENTITY
    target_entities: tuple[str, ...] = ()
    precision_required: str = "normal"
    freshness_seconds: int | None = None
    minimum_evidence_strength: str = "standard"
    independence_required: int = 0
    contradiction_tolerance: str = "must_resolve"
    required_source_families: tuple[str, ...] = ()


@dataclass(frozen=True)
class QueryCandidate:
    query: str
    purpose: str
    expected_information_gain: float
    estimated_cost: float
    target_source_family: str | None = None
    target_claim_ids: tuple[str, ...] = ()
    stop_condition: str = "claim_satisfied"


@dataclass(frozen=True)
class MethodCandidate:
    method_id: str
    source_id: str
    representation: str
    parser: str | None = None
    expected_success: float = 0.5
    expected_completeness: float = 0.5
    evidence_directness: float = 0.5
    authority: float = 0.5
    freshness: float = 0.5
    independence: float = 0.5
    latency_cost: float = 1.0
    resource_cost: float = 1.0
    risk_penalty: float = 0.0
    information_gain: float = 0.5
    prerequisites: tuple[str, ...] = ()


@dataclass(frozen=True)
class ResourceEnvelope:
    search_units: int = 0
    http_requests: int = 0
    pages: int = 0
    browser_seconds: int = 0
    ai_units: int = 0
    ai_calls: int = 0
    bytes_downloaded: int = 0
    artifact_bytes: int = 0
    wall_seconds: int = 0
    concurrency: int = 1
    retries: int = 0
    verification_units: int = 0
    d1_reads: int = 0
    d1_writes: int = 0
    queue_ops: int = 0
    workflow_steps: int = 0
    recovery_reserve_ratio: float = 0.10

    def validate(self) -> None:
        values = self.__dict__.items()
        for name, value in values:
            if name == "recovery_reserve_ratio":
                if not 0 <= float(value) < 1:
                    raise ValueError("recovery_reserve_ratio must be in [0,1)")
            elif int(value) < 0:
                raise ValueError(f"{name} must be non-negative")
        if self.concurrency < 1:
            raise ValueError("concurrency must be positive")


@dataclass(frozen=True)
class Coverage:
    claim_id: str
    state: CoverageState
    evidence_count: int = 0
    independent_origins: int = 0
    freshness_ok: bool = True
    completeness: float = 0.0
    reason: str = ""


@dataclass(frozen=True)
class SourcePlan:
    source_family: str
    required: bool = False
    minimum_origins: int = 0
    representations: tuple[str, ...] = ()
    languages: tuple[str, ...] = ()
    discovery_only: bool = False


@dataclass(frozen=True)
class Action:
    action_id: str
    kind: str
    purpose: str
    claim_ids: tuple[str, ...] = ()
    prerequisites: tuple[str, ...] = ()
    alternatives: tuple[str, ...] = ()
    method_ids: tuple[str, ...] = ()
    estimated_cost: float = 0.0
    side_effect: str = "none"


@dataclass(frozen=True)
class PlanDiagnostics:
    reasons: tuple[str, ...] = ()
    selected_methods: tuple[str, ...] = ()
    rejected_methods: tuple[str, ...] = ()
    stop_reason: StopReason | None = None
    explain: str = ""


@dataclass(frozen=True)
class TaskPlan:
    task_mode: TaskMode
    claims: tuple[ClaimRequirement, ...]
    source_plans: tuple[SourcePlan, ...]
    queries: tuple[QueryCandidate, ...]
    methods: tuple[MethodCandidate, ...]
    actions: tuple[Action, ...]
    envelope: ResourceEnvelope
    metadata: Mapping[str, str] = field(default_factory=dict)
    version: str = "1"


@dataclass(frozen=True)
class SourceProfileHint:
    source_id: str
    supported_representations: tuple[str, ...] = ()
    preferred_method: str | None = None
    pagination: str | None = None
    known_failures: tuple[FailureClass, ...] = ()
    concurrency_ceiling: int | None = None
    health: float = 1.0
    sample_size: int = 0
    last_success_at: str | None = None


def as_sequence(value: Sequence[str] | None) -> tuple[str, ...]:
    return tuple(value or ())
