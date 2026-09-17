from __future__ import annotations
from dataclasses import dataclass
from enum import Enum

class ObservationState(str, Enum):
    ACCEPTED='accepted'; REJECTED='rejected'; ADMITTED='admitted'; NOT_ADMITTED='not_admitted'; CREATED='created'; NOT_CREATED='not_created'; QUEUED='queued'; RUNNING='running'; COMPLETED='completed'; FAILED='failed'; CANCELLED='cancelled'; SKIPPED='skipped'; REACHED='reached'; NOT_REACHED='not_reached'; PARTIAL='partial'; AVAILABLE='available'; UNAVAILABLE='unavailable'; UNKNOWN='unknown'
class EvidenceState(str, Enum):
    NOT_ATTEMPTED='NOT_ATTEMPTED'; UNKNOWN='UNKNOWN'; BLOCKED='BLOCKED'; PARTIAL='PARTIAL'; FAILED='FAILED'; COMPLETE='COMPLETE'
@dataclass(frozen=True)
class WorkflowExecutionObservation:
    trigger: ObservationState; graph: ObservationState; expected_jobs:int|None; created_jobs:int|None; completed_jobs:int|None; failed_jobs:int|None; cancelled_jobs:int|None; skipped_jobs:int|None; artifacts:ObservationState; downstream:ObservationState; diagnostics:ObservationState; first_unobserved_stage:str|None=None
    def validate(self):
        counts=(self.expected_jobs,self.created_jobs,self.completed_jobs,self.failed_jobs,self.cancelled_jobs,self.skipped_jobs)
        if any(v is not None and v<0 for v in counts): raise ValueError('job counts cannot be negative')
        if self.expected_jobs is not None and self.created_jobs is not None and self.created_jobs>self.expected_jobs: raise ValueError('created_jobs cannot exceed expected_jobs')
        if self.completed_jobs is not None and self.created_jobs is not None and self.completed_jobs>self.created_jobs: raise ValueError('completed_jobs cannot exceed created_jobs')
        if self.failed_jobs is not None and self.created_jobs is not None and self.failed_jobs>self.created_jobs: raise ValueError('failed_jobs cannot exceed created_jobs')
def _resolve_state(o):
    if o.trigger is ObservationState.REJECTED:return EvidenceState.BLOCKED,'trigger rejected'
    if o.trigger is ObservationState.UNKNOWN:return EvidenceState.UNKNOWN,'trigger admission was not observed'
    if o.graph is ObservationState.NOT_ADMITTED:return EvidenceState.BLOCKED,'workflow graph was not admitted'
    if o.graph is ObservationState.UNKNOWN:return EvidenceState.UNKNOWN,'workflow graph admission was not observed'
    return _resolve_jobs(o)
def _resolve_jobs(o):
    if o.expected_jobs==0:return EvidenceState.UNKNOWN,'workflow declared no expected jobs; execution cannot be certified from this receipt'
    if o.created_jobs==0 and o.expected_jobs and o.trigger is ObservationState.ACCEPTED:return EvidenceState.UNKNOWN,'trigger was accepted but zero jobs were observed'
    if o.created_jobs is None:return EvidenceState.UNKNOWN,'job creation was not observed'
    if o.expected_jobs is not None and o.created_jobs<o.expected_jobs:return EvidenceState.PARTIAL,'fewer jobs were created than expected'
    if o.failed_jobs and o.failed_jobs>0:return EvidenceState.FAILED,'one or more created jobs failed'
    if o.cancelled_jobs and o.cancelled_jobs>0:return EvidenceState.PARTIAL,'one or more created jobs were cancelled'
    if o.skipped_jobs and o.skipped_jobs>0:return EvidenceState.PARTIAL,'one or more created jobs were skipped'
    if o.completed_jobs is not None and o.expected_jobs is not None and o.completed_jobs<o.expected_jobs:return EvidenceState.PARTIAL,'not all expected jobs completed'
    return _resolve_downstream(o)
def _resolve_downstream(o):
    if o.downstream is ObservationState.NOT_REACHED:return EvidenceState.PARTIAL,'downstream stage was not reached'
    if o.downstream is ObservationState.UNKNOWN:return EvidenceState.UNKNOWN,'downstream reachability was not observed'
    if o.artifacts in {ObservationState.UNKNOWN,ObservationState.UNAVAILABLE}:return EvidenceState.UNKNOWN,'artifact creation evidence was not observed'
    if o.artifacts is ObservationState.NOT_REACHED:return EvidenceState.PARTIAL,'required artifact stage was not reached'
    if o.diagnostics in {ObservationState.UNKNOWN,ObservationState.UNAVAILABLE}:return EvidenceState.UNKNOWN,'diagnostic availability was not observed'
    return EvidenceState.COMPLETE,'all required execution stages were observed'
def compose_workflow_evidence(observation):
    observation.validate(); state,reason=_resolve_state(observation)
    return {'schema':'workflow-execution-evidence/v1','state':state.value,'reason':reason,'trigger':observation.trigger.value,'graph':observation.graph.value,'expected_jobs':observation.expected_jobs,'created_jobs':observation.created_jobs,'completed_jobs':observation.completed_jobs,'failed_jobs':observation.failed_jobs,'cancelled_jobs':observation.cancelled_jobs,'skipped_jobs':observation.skipped_jobs,'artifacts':observation.artifacts.value,'downstream':observation.downstream.value,'diagnostics':observation.diagnostics.value,'first_unobserved_stage':observation.first_unobserved_stage,'production_claim_allowed':state is EvidenceState.COMPLETE,'root_cause_inferred':False}
