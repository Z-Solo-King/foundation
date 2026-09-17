import pytest
from backend.workflow_evidence import EvidenceState, ObservationState, WorkflowExecutionObservation, compose_workflow_evidence

def observation(**changes):
    data=dict(trigger=ObservationState.ACCEPTED,graph=ObservationState.ADMITTED,expected_jobs=3,created_jobs=3,completed_jobs=3,failed_jobs=0,cancelled_jobs=0,skipped_jobs=0,artifacts=ObservationState.CREATED,downstream=ObservationState.REACHED,diagnostics=ObservationState.AVAILABLE)
    data.update(changes); return WorkflowExecutionObservation(**data)

def test_complete_requires_all_observed_stages():
    r=compose_workflow_evidence(observation()); assert r['schema']=='workflow-execution-evidence/v1'; assert r['state']==EvidenceState.COMPLETE.value; assert r['production_claim_allowed'] is True; assert r['root_cause_inferred'] is False

def test_zero_jobs_after_accepted_trigger_is_unknown_not_failed():
    r=compose_workflow_evidence(observation(created_jobs=0,completed_jobs=0)); assert r['state']==EvidenceState.UNKNOWN.value; assert 'zero jobs' in r['reason']; assert r['production_claim_allowed'] is False

def test_unknown_trigger_and_graph_admission_are_unknown():
    a=compose_workflow_evidence(observation(trigger=ObservationState.UNKNOWN,graph=ObservationState.ADMITTED,created_jobs=None,completed_jobs=None)); b=compose_workflow_evidence(observation(graph=ObservationState.UNKNOWN,created_jobs=None,completed_jobs=None)); c=compose_workflow_evidence(observation(graph=ObservationState.NOT_ADMITTED,created_jobs=None,completed_jobs=None)); assert a['state']==EvidenceState.UNKNOWN.value; assert b['state']==EvidenceState.UNKNOWN.value; assert c['state']==EvidenceState.BLOCKED.value

def test_partial_job_creation_preserves_partial_state():
    r=compose_workflow_evidence(observation(created_jobs=2,completed_jobs=2)); assert r['state']==EvidenceState.PARTIAL.value

def test_expected_zero_and_unobserved_job_creation_are_unknown():
    assert compose_workflow_evidence(observation(expected_jobs=0,created_jobs=0,completed_jobs=0))['state']==EvidenceState.UNKNOWN.value; assert compose_workflow_evidence(observation(created_jobs=None,completed_jobs=None))['state']==EvidenceState.UNKNOWN.value

def test_failed_job_is_failed_not_complete():
    assert compose_workflow_evidence(observation(completed_jobs=2,failed_jobs=1))['state']==EvidenceState.FAILED.value

def test_cancelled_or_skipped_job_is_partial():
    assert compose_workflow_evidence(observation(completed_jobs=2,cancelled_jobs=1))['state']==EvidenceState.PARTIAL.value; assert compose_workflow_evidence(observation(completed_jobs=2,skipped_jobs=1))['state']==EvidenceState.PARTIAL.value

def test_incomplete_completed_count_is_partial():
    assert compose_workflow_evidence(observation(completed_jobs=2))['state']==EvidenceState.PARTIAL.value

def test_downstream_states_are_preserved():
    assert compose_workflow_evidence(observation(downstream=ObservationState.NOT_REACHED))['state']==EvidenceState.PARTIAL.value; assert compose_workflow_evidence(observation(downstream=ObservationState.UNKNOWN))['state']==EvidenceState.UNKNOWN.value

def test_artifact_and_diagnostics_states_are_preserved():
    for s in (ObservationState.UNKNOWN,ObservationState.UNAVAILABLE): assert compose_workflow_evidence(observation(artifacts=s))['state']==EvidenceState.UNKNOWN.value; assert compose_workflow_evidence(observation(diagnostics=s))['state']==EvidenceState.UNKNOWN.value
    assert compose_workflow_evidence(observation(artifacts=ObservationState.NOT_REACHED))['state']==EvidenceState.PARTIAL.value

def test_rejected_trigger_is_blocked():
    assert compose_workflow_evidence(observation(trigger=ObservationState.REJECTED,graph=ObservationState.UNKNOWN,created_jobs=None,completed_jobs=None))['state']==EvidenceState.BLOCKED.value

@pytest.mark.parametrize(('changes','message'),[({'created_jobs':-1},'job counts cannot be negative'),({'created_jobs':4},'created_jobs cannot exceed expected_jobs'),({'created_jobs':2,'completed_jobs':3},'completed_jobs cannot exceed created_jobs'),({'created_jobs':2,'completed_jobs':2,'failed_jobs':3},'failed_jobs cannot exceed created_jobs')])
def test_invalid_counts_raise(changes,message):
    with pytest.raises(ValueError,match=message): compose_workflow_evidence(observation(**changes))
