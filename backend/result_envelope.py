"""Versioned public-safe result envelope for Heroic AI/research outcomes."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, Mapping


class ResultStatus(StrEnum):
    COMPLETED = "COMPLETED"
    PARTIAL = "PARTIAL"
    DEGRADED = "DEGRADED"
    BLOCKED = "BLOCKED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class FreshnessState(StrEnum):
    FRESH = "FRESH"
    STALE = "STALE"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class ResultEnvelope:
    """Stable public result contract independent of provider/runtime internals."""

    schema_version: str = "heroic-ai-result/v1"
    status: ResultStatus = ResultStatus.COMPLETED
    result: Any = None
    requested_scope: tuple[str, ...] = ()
    completed_scope: tuple[str, ...] = ()
    missing_scope: tuple[str, ...] = ()
    failed_scope: tuple[str, ...] = ()
    claim_support: Mapping[str, str] = field(default_factory=dict)
    warnings: tuple[str, ...] = ()
    limitations: tuple[str, ...] = ()
    freshness: FreshnessState = FreshnessState.UNKNOWN
    provenance_refs: tuple[str, ...] = ()
    execution_identity: str | None = None

    def validate(self) -> None:
        if self.schema_version != "heroic-ai-result/v1":
            raise ValueError("unsupported result envelope schema")
        if self.status is ResultStatus.COMPLETED:
            if self.missing_scope or self.failed_scope:
                raise ValueError("COMPLETED results cannot contain missing or failed scope")
            if any(value.upper() in {"UNVERIFIED", "UNKNOWN", "CONTRADICTED", "STALE"} for value in self.claim_support.values()):
                raise ValueError("COMPLETED results cannot contain unresolved claim support states")
            if self.freshness is FreshnessState.STALE:
                raise ValueError("COMPLETED results cannot present stale evidence as fresh")
        if self.execution_identity is not None and not self.execution_identity.strip():
            raise ValueError("execution_identity must be non-empty when provided")

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        return {
            "schema_version": self.schema_version,
            "status": self.status.value,
            "result": self.result,
            "scope": {
                "requested": list(self.requested_scope),
                "completed": list(self.completed_scope),
                "missing": list(self.missing_scope),
                "failed": list(self.failed_scope),
            },
            "claim_support": dict(self.claim_support),
            "warnings": list(self.warnings),
            "limitations": list(self.limitations),
            "freshness": self.freshness.value,
            "provenance_refs": list(self.provenance_refs),
            "execution_identity": self.execution_identity,
        }


def envelope_from_legacy_response(
    *,
    ok: bool,
    result: Any = None,
    error: str | None = None,
    run_id: str | None = None,
    metadata: Mapping[str, Any] | None = None,
) -> ResultEnvelope:
    """Adapt the legacy API response shape without duplicating business logic."""
    payload = dict(metadata or {})
    if run_id:
        payload.setdefault("run_id", run_id)
    if ok:
        return ResultEnvelope(result=result if result is not None else payload)
    return ResultEnvelope(
        status=ResultStatus.FAILED,
        result=None,
        warnings=(error,) if error else (),
        limitations=("legacy_error_response",),
    )
