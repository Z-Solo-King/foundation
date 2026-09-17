from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Literal

ExecutionState = Literal["NOT_ATTEMPTED", "UNKNOWN", "BLOCKED", "PARTIAL", "FAILED", "COMPLETE"]
_VALID = frozenset({"NOT_ATTEMPTED", "UNKNOWN", "BLOCKED", "PARTIAL", "FAILED", "COMPLETE"})


@dataclass(frozen=True)
class WorkflowEvidenceReceipt:
    """Immutable evidence of what a workflow actually executed."""

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
        if self.schema != "workflow-evidence-receipt/v1":
            raise ValueError("unsupported workflow evidence schema")
        if not all(isinstance(v, str) and v.strip() for v in (self.workflow, self.revision, self.run_id)):
            raise ValueError("workflow identity is required")
        if not isinstance(self.job_count, int) or self.job_count < 0:
            raise ValueError("job_count cannot be negative")
        states = (self.trigger_state, self.graph_state, self.job_state, self.step_state,
                  self.artifact_state, self.downstream_state, self.diagnostic_state)
        if any(state not in _VALID for state in states):
            raise ValueError("invalid workflow evidence state")
        if self.job_count == 0 and self.job_state == "COMPLETE":
            raise ValueError("zero-job workflow cannot have COMPLETE job state")
        if self.job_count == 0 and self.graph_state == "COMPLETE":
            raise ValueError("zero-job workflow cannot imply complete admitted execution")

    @property
    def aggregate_state(self) -> ExecutionState:
        self.validate()
        states = (self.trigger_state, self.graph_state, self.job_state, self.step_state,
                  self.artifact_state, self.downstream_state)
        if any(s == "FAILED" for s in states):
            return "PARTIAL" if any(s == "COMPLETE" for s in states) else "FAILED"
        if any(s == "BLOCKED" for s in states):
            return "BLOCKED"
        if any(s in {"UNKNOWN", "NOT_ATTEMPTED"} for s in states):
            return "PARTIAL" if any(s == "COMPLETE" for s in states) else "UNKNOWN"
        return "COMPLETE"

    def digest(self) -> str:
        payload = dict(self.__dict__)
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
        return hashlib.sha256(canonical).hexdigest()
