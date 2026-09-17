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
        for value in (self.expected_jobs, self.created_jobs, self.completed_jobs, self.failed_jobs, self.cancelled_jobs, self.skipped_jobs):
            if value is not None and value < 0:
                raise ValueError("job counts cannot be negative")
        if self.expected_jobs is not None and self.created_jobs is not None and self.created_jobs > self.expected_jobs:
            raise ValueError("created_jobs cannot exceed expected_jobs")
        if self.completed_jobs is not None and self.created_jobs is not None and self.completed_jobs > self.created_jobs:
            raise ValueError("completed_jobs cannot exceed created_jobs")
        if self.failed_jobs is not None and self.created_jobs is not None and self.failed_jobs > self.created_jobs:
            raise ValueError("failed_jobs cannot exceed created_jobs")


def compose_workflow_evidence(observation: WorkflowExecutionObservation) -> dict[str, object]:
    observation.validate()

    if observation.trigger is ObservationState.REJECTED:
        state = EvidenceState.BLOCKED
        reason = "trigger rejected"
    elif observation.trigger is ObservationState.UNKNOWN:
        state = EvidenceState.UNKNOWN
        reason = "trigger admission was not observed"
    elif observation.graph is ObservationState.NOT_ADMITTED:
        state = EvidenceState.BLOCKED
        reason = "workflow graph was not admitted"
    elif observation.graph is ObservationState.UNKNOWN:
        state = EvidenceState.UNKNOWN
        reason = "workflow graph admission was not observed"
    elif observation.expected_jobs == 0:
        state = EvidenceState.UNKNOWN
        reason = "workflow declared no expected jobs; execution cannot be certified from this receipt"
    elif observation.created_jobs == 0 and observation.expected_jobs and observation.trigger is ObservationState.ACCEPTED:
        state = EvidenceState.UNKNOWN
        reason = "trigger was accepted but zero jobs were observed"
    elif observation.created_jobs is None:
        state = EvidenceState.UNKNOWN
        reason = "job creation was not observed"
    elif observation.expected_jobs is not None and observation.created_jobs < observation.expected_jobs:
        state = EvidenceState.PARTIAL
        reason = "fewer jobs were created than expected"
    elif observation.failed_jobs and observation.failed_jobs > 0:
        state = EvidenceState.FAILED
        reason = "one or more created jobs failed"
    elif observation.cancelled_jobs and observation.cancelled_jobs > 0:
        state = EvidenceState.PARTIAL
        reason = "one or more created jobs were cancelled"
    elif observation.skipped_jobs and observation.skipped_jobs > 0:
        state = EvidenceState.PARTIAL
        reason = "one or more created jobs were skipped"
    elif observation.completed_jobs is not None and observation.expected_jobs is not None and observation.completed_jobs < observation.expected_jobs:
        state = EvidenceState.PARTIAL
        reason = "not all expected jobs completed"
    elif observation.downstream is ObservationState.NOT_REACHED:
        state = EvidenceState.PARTIAL
        reason = "downstream stage was not reached"
    elif observation.downstream is ObservationState.UNKNOWN:
        state = EvidenceState.UNKNOWN
        reason = "downstream reachability was not observed"
    elif observation.artifacts in {ObservationState.UNKNOWN, ObservationState.UNAVAILABLE}:
        state = EvidenceState.UNKNOWN
        reason = "artifact creation evidence was not observed"
    elif observation.artifacts is ObservationState.NOT_REACHED:
        state = EvidenceState.PARTIAL
        reason = "required artifact stage was not reached"
    elif observation.diagnostics in {ObservationState.UNKNOWN, ObservationState.UNAVAILABLE}:
        state = EvidenceState.UNKNOWN
        reason = "diagnostic availability was not observed"
    else:
        state = EvidenceState.COMPLETE
        reason = "all required execution stages were observed"

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
