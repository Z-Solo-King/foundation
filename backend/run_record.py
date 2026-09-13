"""Privacy-safe aggregate records for public research/chatbot executions."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from backend.stage_receipt import StageReceipt, validate_chain

MAX_FIELD_COUNT = 128
MAX_ARTIFACT_COUNT = 256
MAX_SOURCE_COUNT = 128
MAX_LEARNING_NOTE = 1024
ALLOWED_RESULT_STATUS = frozenset({"success", "partial", "blocked", "unknown", "rejected", "error", "cancelled"})


@dataclass(frozen=True)
class RouteAttempt:
    method: str
    status: str
    reason_allowed: str = ""
    http_status: int | None = None
    retryable: bool = False
    fallback_eligible: bool = False


@dataclass(frozen=True)
class ResourceUsage:
    resource_units: int = 0
    network_requests: int = 0
    bytes: int = 0
    ai_units: int = 0
    wall_time_ms: int = 0
    quota_state: str = "unknown"

    def validate(self) -> None:
        for name, value in asdict(self).items():
            if name != "quota_state" and value < 0:
                raise ValueError(f"{name} must be non-negative")
        if not self.quota_state.strip():
            raise ValueError("quota_state must not be empty")


@dataclass(frozen=True)
class EvidenceSelectionMetrics:
    planned_context_units: int = 0
    retained_evidence_units: int = 0
    dropped_evidence_units: int = 0
    duplicate_evidence_dropped: int = 0
    selected_evidence_count: int = 0
    source_count: int = 0

    def validate(self) -> None:
        for name, value in asdict(self).items():
            if value < 0:
                raise ValueError(f"{name} must be non-negative")
        if self.retained_evidence_units + self.dropped_evidence_units > self.planned_context_units:
            raise ValueError("evidence units exceed planned context units")
        if self.selected_evidence_count > 0 and self.source_count == 0:
            raise ValueError("selected evidence requires at least one source")


@dataclass(frozen=True)
class TokenEfficiencyMetrics:
    estimated_input_tokens: int = 0
    estimated_output_tokens: int = 0
    model_calls: int = 0
    cache_hits: int = 0
    deterministic_steps: int = 0
    accepted: bool = False

    def validate(self) -> None:
        for name, value in asdict(self).items():
            if name != "accepted" and value < 0:
                raise ValueError(f"{name} must be non-negative")
        if self.cache_hits > self.model_calls:
            raise ValueError("cache_hits cannot exceed model_calls")

    @property
    def total_estimated_tokens(self) -> int:
        return self.estimated_input_tokens + self.estimated_output_tokens


@dataclass(frozen=True)
class RunResult:
    status: str
    failure_class: str | None = None
    answer_artifact_ref: str | None = None

    def validate(self) -> None:
        if self.status not in ALLOWED_RESULT_STATUS:
            raise ValueError("unsupported run result status")


@dataclass(frozen=True)
class ChatbotRunRecord:
    schema_version: str
    run_id: str
    created_at: str
    request_fingerprint: str
    intent: dict[str, Any]
    method_selected: str
    method_reason: str
    stages: tuple[StageReceipt, ...]
    result: RunResult
    software: dict[str, str | None]
    resource_usage: ResourceUsage
    started_at: str | None = None
    finished_at: str | None = None
    requested_fields: tuple[str, ...] = ()
    attempts: tuple[RouteAttempt, ...] = ()
    sources: tuple[dict[str, Any], ...] = ()
    evidence: tuple[dict[str, Any], ...] = ()
    artifacts: tuple[dict[str, Any], ...] = ()
    learning_note: str | None = None
    evidence_selection: EvidenceSelectionMetrics | None = None
    token_efficiency: TokenEfficiencyMetrics | None = None

    def validate(self) -> None:
        if not self.run_id.strip() or not self.request_fingerprint.strip():
            raise ValueError("run_id and request_fingerprint must not be empty")
        if len(self.requested_fields) > MAX_FIELD_COUNT:
            raise ValueError("requested_fields limit exceeded")
        if len(self.sources) > MAX_SOURCE_COUNT:
            raise ValueError("sources limit exceeded")
        if len(self.artifacts) > MAX_ARTIFACT_COUNT:
            raise ValueError("artifacts limit exceeded")
        if self.learning_note is not None and len(self.learning_note) > MAX_LEARNING_NOTE:
            raise ValueError("learning_note exceeds bounded length")
        self.result.validate()
        self.resource_usage.validate()
        if self.evidence_selection is not None:
            self.evidence_selection.validate()
        if self.token_efficiency is not None:
            self.token_efficiency.validate()
        if not self.stages:
            raise ValueError("at least one stage receipt is required")
        if not validate_chain(self.stages):
            raise ValueError("stage receipt chain is invalid")
        if any(receipt.request_fingerprint != self.request_fingerprint for receipt in self.stages):
            raise ValueError("stage/request fingerprint mismatch")

    def to_public_metadata(self) -> dict[str, Any]:
        self.validate()
        metadata: dict[str, Any] = {
            "schema_version": self.schema_version,
            "run_id": self.run_id,
            "created_at": self.created_at,
            "request_fingerprint": self.request_fingerprint,
            "method_selected": self.method_selected,
            "result_status": self.result.status,
            "failure_class": self.result.failure_class,
            "stage_count": len(self.stages),
            "source_count": len(self.sources),
            "evidence_count": len(self.evidence),
            "artifact_count": len(self.artifacts),
            "resource_usage": asdict(self.resource_usage),
            "software": dict(self.software),
        }
        if self.evidence_selection is not None:
            metadata["evidence_selection"] = asdict(self.evidence_selection)
        if self.token_efficiency is not None:
            metadata["token_efficiency"] = asdict(self.token_efficiency)
            metadata["token_efficiency"]["total_estimated_tokens"] = self.token_efficiency.total_estimated_tokens
        return metadata
