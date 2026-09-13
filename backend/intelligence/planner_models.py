from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Mapping, Sequence

class TaskMode(Enum):
    FACT="fact"; SPECIFICATION="specification"; COMPARISON="comparison"; RECOMMENDATION="recommendation"; PRICE_AVAILABILITY="price_availability"; TEMPORAL="temporal"; CONTRADICTION="contradiction"; DIAGNOSIS="diagnosis"; COMMUNITY="community"; PRIMARY_SOURCE="primary_source"; ENTITY_RESOLUTION="entity_resolution"; CODE="code"; DATA="data"; DOCUMENT="document"; MEDIA="media"; MIXED="mixed"
class FactType(Enum):
    IDENTITY="identity"; SPECIFICATION="specification"; COMMERCIAL="commercial"; AVAILABILITY="availability"; TEMPORAL="temporal"; RELATIONAL="relational"; QUALITATIVE="qualitative"; NORMATIVE="normative"
class CoverageState(Enum):
    SATISFIED="satisfied"; SUPPORTED="supported"; PARTIAL="partial"; UNSUPPORTED="unsupported"; CONTRADICTED="contradicted"; STALE="stale"; BLOCKED="blocked"; INACCESSIBLE="inaccessible"; AMBIGUOUS="ambiguous"
class FailureClass(Enum):
    TRANSPORT="transport"; TIMEOUT="timeout"; RATE_LIMITED="429"; RATE_LIMIT="rate_limit"; AUTH="auth"; AUTH_REQUIRED="401"; FORBIDDEN="403"; CAPTCHA="captcha"; POLICY="policy"; PARSER="parser"; MALFORMED="malformed"; ENCODING="encoding_error"; SCHEMA="schema"; PARTIAL="partial"; EMPTY="empty"; NOT_FOUND="not_found"; BLOCKED="blocked"; QUOTA="quota"; FRESHNESS="freshness"; CONTRADICTION="contradiction"; LOW_YIELD="low_yield"
class PaginationKind(Enum):
    PAGE="page"; CURSOR="cursor"; OFFSET="offset"; TOKEN="token"; UNKNOWN="unknown"
class StopReason(Enum):
    QUALITY_FLOOR="quality_floor"; BUDGET_EXHAUSTED="budget_exhausted"; LOW_INFORMATION_GAIN="low_information_gain"; CONTRADICTION_OPEN="contradiction_open"; UNSATISFIED="unsatisfied"; COMPLETE="complete"

_FAILURE_ALIASES: dict[str, FailureClass] = {
    "404": FailureClass.NOT_FOUND,
    "not_found": FailureClass.NOT_FOUND,
    "future": FailureClass.FRESHNESS,
    "freshness": FailureClass.FRESHNESS,
    "429": FailureClass.RATE_LIMITED,
    "rate_limit": FailureClass.RATE_LIMIT,
    "401": FailureClass.AUTH_REQUIRED,
    "403": FailureClass.FORBIDDEN,
    "captcha": FailureClass.CAPTCHA,
    "encoding_error": FailureClass.ENCODING,
    "malformed": FailureClass.MALFORMED,
    "partial": FailureClass.PARTIAL,
}

def coerce_failure_class(value: FailureClass | str | None) -> FailureClass | None:
    if value is None:
        return None
    if isinstance(value, FailureClass):
        return value
    normalized = str(value).strip().lower()
    try:
        return FailureClass(normalized)
    except ValueError:
        return _FAILURE_ALIASES.get(normalized)

@dataclass(frozen=True)
class ClaimRequirement:
    claim_id: str; text: str; fact_type: FactType=FactType.IDENTITY; target_entities: tuple[str,...]=(); precision_required: str="normal"; freshness_seconds: int|None=None; minimum_evidence_strength: str="standard"; independence_required: int=0; contradiction_tolerance: str="must_resolve"; required_source_families: tuple[str,...]=()
@dataclass(frozen=True)
class FieldRequirement:
    field_id: str; semantic_name: str; required: bool=True; exact: bool=False; preferred_representations: tuple[str,...]=(); allow_inference: bool=False; source_families: tuple[str,...]=()
@dataclass(frozen=True)
class QueryCandidate:
    query: str; purpose: str; expected_information_gain: float; estimated_cost: float; target_source_family: str|None=None; target_claim_ids: tuple[str,...]=(); stop_condition: str="claim_satisfied"
@dataclass(frozen=True)
class MethodCandidate:
    method_id: str; source_id: str; representation: str; parser: str|None=None; expected_success: float=.5; expected_completeness: float=.5; evidence_directness: float=.5; authority: float=.5; freshness: float=.5; independence: float=.5; latency_cost: float=1.; resource_cost: float=1.; risk_penalty: float=0.; information_gain: float=.5; prerequisites: tuple[str,...]=()
@dataclass(frozen=True)
class ResourceEnvelope:
    search_units: int=0; http_requests: int=0; pages: int=0; browser_seconds: int=0; ai_units: int=0; ai_calls: int=0; bytes_downloaded: int=0; artifact_bytes: int=0; wall_seconds: int=0; concurrency: int=1; retries: int=0; verification_units: int=0; d1_reads: int=0; d1_writes: int=0; queue_ops: int=0; workflow_steps: int=0; recovery_reserve_ratio: float=.10
    def validate(self)->None:
        for name,value in self.__dict__.items():
            if name=="recovery_reserve_ratio":
                ratio=float(value)
                if ratio<0:
                    raise ValueError("recovery_reserve_ratio must be in [0,1)")
                if ratio>=1:
                    raise ValueError("recovery_reserve_ratio must be in [0,1)")
            else:
                numeric=int(value)
                if numeric<0:
                    raise ValueError(f"{name} must be non-negative")
        if self.concurrency<1:
            raise ValueError("concurrency must be positive")
@dataclass(frozen=True)
class Coverage:
    claim_id: str; state: CoverageState; evidence_count: int=0; independent_origins: int=0; freshness_ok: bool=True; completeness: float=0.; reason: str=""
@dataclass(frozen=True)
class SourcePlan:
    source_family: str; required: bool=False; minimum_origins: int=0; representations: tuple[str,...]=(); languages: tuple[str,...]=(); discovery_only: bool=False
@dataclass(frozen=True)
class Action:
    action_id: str; kind: str; purpose: str; claim_ids: tuple[str,...]=(); field_ids: tuple[str,...]=(); prerequisites: tuple[str,...]=(); alternatives: tuple[str,...]=(); method_ids: tuple[str,...]=(); estimated_cost: float=0.; side_effect: str="none"
@dataclass(frozen=True)
class PlanDiagnostics:
    reasons: tuple[str,...]=(); selected_methods: tuple[str,...]=(); rejected_methods: tuple[str,...]=(); stop_reason: StopReason|None=None; explain: str=""
@dataclass(frozen=True)
class TaskPlan:
    task_mode: TaskMode; claims: tuple[ClaimRequirement,...]; fields: tuple[FieldRequirement,...]; source_plans: tuple[SourcePlan,...]; queries: tuple[QueryCandidate,...]; methods: tuple[MethodCandidate,...]; actions: tuple[Action,...]; envelope: ResourceEnvelope; metadata: Mapping[str,str]=field(default_factory=dict); version: str="1"
@dataclass(frozen=True)
class SourceProfileHint:
    source_id: str; supported_representations: tuple[str,...]=(); preferred_method: str|None=None; pagination: str|None=None; known_failures: tuple[FailureClass,...]=(); concurrency_ceiling: int|None=None; health: float=1.; sample_size: int=0; last_success_at: str|None=None

def as_sequence(value: Sequence[str]|None)->tuple[str,...]:
    return tuple(value or ())
