from __future__ import annotations
from dataclasses import dataclass
from typing import Literal

ExecutionState = Literal["NOT_ATTEMPTED", "UNKNOWN", "BLOCKED", "PARTIAL", "FAILED", "COMPLETE"]

@dataclass(frozen=True)
class WorkflowEvidenceReceipt:
    schema: str
    workflow: str
    revision: str
    run_id: str
    trigger_state: ExecutionState
    graph_state: ExecutionState
    job_count: int
    job_state: ExecutionState
    step_state: ExecutionState
    artifact_state: ExecutionState
    downstream_state: ExecutionState
    diagnostic_state: ExecutionState

    def validate(self) -> None:
        if self.schema != "workflow-evidence-receipt/v1": raise ValueError("unsupported workflow evidence schema")
        if not all(isinstance(value, str) and value.strip() for value in (self.workflow, self.revision, self.run_id)): raise ValueError("workflow identity is required")
        if self.job_count < 0: raise ValueError("job_count cannot be negative")
        states = (self.trigger_state, self.graph_state, self.job_state, self.step_state, self.artifact_state, self.downstream_state, self.diagnostic_state)
        valid = {"NOT_ATTEMPTED", "UNKNOWN", "BLOCKED", "PARTIAL", "FAILED", "COMPLETE"}
        if any(state not in valid for state in states): raise ValueError("invalid workflow evidence state")
        if self.job_count == 0 and self.job_state == "COMPLETE": raise ValueError("zero-job workflow cannot have COMPLETE job state")
        if self.job_count == 0 and self.graph_state == "COMPLETE": raise ValueError("zero-job workflow cannot imply complete admitted execution")

    @property
    def aggregate_state(self) -> ExecutionState:
        self.validate()
        states = (self.trigger_state, self.graph_state, self.job_state, self.step_state, self.artifact_state, self.downstream_state)
        if any(state == "FAILED" for state in states): return "PARTIAL" if any(state == "COMPLETE" for state in states) else "FAILED"
        if any(state == "BLOCKED" for state in states): return "BLOCKED"
        if any(state in {"UNKNOWN", "NOT_ATTEMPTED"} for state in states): return "PARTIAL" if any(state == "COMPLETE" for state in states) else "UNKNOWN"
        return "COMPLETE"
