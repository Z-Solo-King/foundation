from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ObservationState(str, Enum):
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    ADMITTED = "admitted"
    NOT_ADMITTED = "not_admitted"
    CREATED = "created"
    NOT_CREATED = "not_created"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    SKIPPED = "skipped"
    REACHED = "reached"
    NOT_REACHED = "not_reached"
    PARTIAL = "partial"
    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"
    UNKNOWN = "unknown"


class EvidenceState(str, Enum):
    NOT_ATTEMPTED = "NOT_ATTEMPTED"
    UNKNOWN = "UNKNOWN"
    BLOCKED = "BLOCKED"
    PARTIAL = "PARTIAL"
    FAILED = "FAILED"
    COMPLETE = "COMPLETE"


@dataclass(frozen=True)
class WorkflowExecutionObservation:
    trigger: ObservationState
    graph: ObservationState
    expected_jobs: int | None
    created_jobs: int | None
    completed_jobs: int | None
    failed_jobs: int | None
    cancelled_jobs: int | None
    skipped_jobs: int | None
    artifacts: ObservationState
    downstream: ObservationState
    diagnostics: ObservationState
    first_unobserved_stage: str | None = None

    def validate(self) -> None:
        counts = (
            self.expected_jobs,
            self.created_jobs,
            self.completed_jobs,
            self.failed_jobs,
            self.cancelled_jobs,
            self.skipped_jobs,
        )
        if any(value is not None and value < 0 for value in counts):
            raise ValueError("job counts cannot be negative")
        if self.expected_jobs is not None and self.created_jobs is not None and self.created_jobs > self.expected_jobs:
            raise ValueError("created_jobs cannot exceed expected_jobs")
        if self.completed_jobs is not None and self.created_jobs is not None and self.completed_jobs > self.created_jobs:
            raise ValueError("completed_jobs cannot exceed created_jobs")
        if self.failed_jobs is not None and self.created_jobs is not None and self.failed_jobs > self.created_jobs:
            raise ValueError("failed_jobs cannot exceed created_jobs")


def _resolve_state(observation: WorkflowExecutionObservation) -> tuple[EvidenceState, str]:
    if observation.trigger is ObservationState.REJECTED:
        return EvidenceState.BLOCKED, "trigger rejected"
    if observation.trigger is ObservationState.UNKNOWN:
        return EvidenceState.UNKNOWN, "trigger admission was not observed"
    if observation.graph is ObservationState.NOT_ADMITTED:
        return EvidenceState.BLOCKED, "workflow graph was not admitted"
    if observation.graph is ObservationState.UNKNOWN:
        return EvidenceState.UNKNOWN, "workflow graph admission was not observed"
    return _resolve_jobs(observation)


def _resolve_jobs(observation: WorkflowExecutionObservation) -> tuple[EvidenceState, str]:
    if observation.expected_jobs == 0:
        return EvidenceState.UNKNOWN, "workflow declared no expected jobs; execution cannot be certified from this receipt"
    if observation.created_jobs == 0 and observation.expected_jobs and observation.trigger is ObservationState.ACCEPTED:
        return EvidenceState.UNKNOWN, "trigger was accepted but zero jobs were observed"
    if observation.created_jobs is None:
        return EvidenceState.UNKNOWN, "job creation was not observed"
    if observation.expected_jobs is not None and observation.created_jobs < observation.expected_jobs:
        return EvidenceState.PARTIAL, "fewer jobs were created than expected"
    if observation.failed_jobs and observation.failed_jobs > 0:
        return EvidenceState.FAILED, "one or more created jobs failed"
    if observation.cancelled_jobs and observation.cancelled_jobs > 0:
        return EvidenceState.PARTIAL, "one or more created jobs were cancelled"
    if observation.skipped_jobs and observation.skipped_jobs > 0:
        return EvidenceState.PARTIAL, "one or more created jobs were skipped"
    if observation.completed_jobs is not None and observation.expected_jobs is not None and observation.completed_jobs < observation.expected_jobs:
        return EvidenceState.PARTIAL, "not all expected jobs completed"
    return _resolve_downstream(observation)


def _resolve_downstream(observation: WorkflowExecutionObservation) -> tuple[EvidenceState, str]:
    if observation.downstream is ObservationState.NOT_REACHED:
        return EvidenceState.PARTIAL, "downstream stage was not reached"
    if observation.downstream is ObservationState.UNKNOWN:
        return EvidenceState.UNKNOWN, "downstream reachability was not observed"
    if observation.artifacts in {ObservationState.UNKNOWN, ObservationState.UNAVAILABLE}:
        return EvidenceState.UNKNOWN, "artifact creation evidence was not observed"
    if observation.artifacts is ObservationState.NOT_REACHED:
        return EvidenceState.PARTIAL, "required artifact stage was not reached"
    if observation.diagnostics in {ObservationState.UNKNOWN, ObservationState.UNAVAILABLE}:
        return EvidenceState.UNKNOWN, "diagnostic availability was not observed"
    return EvidenceState.COMPLETE, "all required execution stages were observed"


def _receipt(observation: WorkflowExecutionObservation, state: EvidenceState, reason: str) -> dict[str, object]:
    return {
        "schema": "workflow-execution-evidence/v1",
        "state": state.value,
        "reason": reason,
        "trigger": observation.trigger.value,
        "graph": observation.graph.value,
        "expected_jobs": observation.expected_jobs,
        "created_jobs": observation.created_jobs,
        "completed_jobs": observation.completed_jobs,
        "failed_jobs": observation.failed_jobs,
        "cancelled_jobs": observation.cancelled_jobs,
        "skipped_jobs": observation.skipped_jobs,
        "artifacts": observation.artifacts.value,
        "downstream": observation.downstream.value,
        "diagnostics": observation.diagnostics.value,
        "first_unobserved_stage": observation.first_unobserved_stage,
        "production_claim_allowed": state is EvidenceState.COMPLETE,
        "root_cause_inferred": False,
    }


def compose_workflow_evidence(observation: WorkflowExecutionObservation) -> dict[str, object]:
    """Compose a truthful receipt without inferring an unobserved root cause."""
    observation.validate()
    state, reason = _resolve_state(observation)
    return _receipt(observation, state, reason)
