import pytest

from backend.workflow_evidence import (
    EvidenceState,
    ObservationState,
    WorkflowExecutionObservation,
    compose_workflow_evidence,
)


def observation(**changes):
    data = dict(
        trigger=ObservationState.ACCEPTED,
        graph=ObservationState.ADMITTED,
        expected_jobs=3,
        created_jobs=3,
        completed_jobs=3,
        failed_jobs=0,
        cancelled_jobs=0,
        skipped_jobs=0,
        artifacts=ObservationState.CREATED,
        downstream=ObservationState.REACHED,
        diagnostics=ObservationState.AVAILABLE,
    )
    data.update(changes)
    return WorkflowExecutionObservation(**data)


def test_complete_requires_all_observed_stages():
    receipt = compose_workflow_evidence(observation())
    assert receipt["schema"] == "workflow-execution-evidence/v1"
    assert receipt["state"] == EvidenceState.COMPLETE.value
    assert receipt["production_claim_allowed"] is True
    assert receipt["root_cause_inferred"] is False


def test_zero_jobs_after_accepted_trigger_is_unknown_not_failed():
    receipt = compose_workflow_evidence(observation(created_jobs=0, completed_jobs=0))
    assert receipt["state"] == EvidenceState.UNKNOWN.value
    assert "zero jobs" in receipt["reason"]
    assert receipt["production_claim_allowed"] is False


def test_unknown_graph_is_unknown_not_inferred_failure():
    receipt = compose_workflow_evidence(observation(graph=ObservationState.UNKNOWN, created_jobs=None, completed_jobs=None))
    assert receipt["state"] == EvidenceState.UNKNOWN.value
    assert "graph admission" in receipt["reason"]
    assert receipt["root_cause_inferred"] is False


def test_partial_job_creation_preserves_partial_state():
    receipt = compose_workflow_evidence(observation(created_jobs=2, completed_jobs=2))
    assert receipt["state"] == EvidenceState.PARTIAL.value
    assert "fewer jobs" in receipt["reason"]


def test_failed_job_is_failed_not_complete():
    receipt = compose_workflow_evidence(observation(completed_jobs=2, failed_jobs=1))
    assert receipt["state"] == EvidenceState.FAILED.value
    assert receipt["production_claim_allowed"] is False


def test_cancelled_or_skipped_job_is_partial():
    cancelled = compose_workflow_evidence(observation(completed_jobs=2, cancelled_jobs=1))
    skipped = compose_workflow_evidence(observation(completed_jobs=2, skipped_jobs=1))
    assert cancelled["state"] == EvidenceState.PARTIAL.value
    assert skipped["state"] == EvidenceState.PARTIAL.value


def test_downstream_and_artifact_unknown_states_are_preserved():
    downstream = compose_workflow_evidence(observation(downstream=ObservationState.UNKNOWN))
    artifacts = compose_workflow_evidence(observation(artifacts=ObservationState.UNKNOWN))
    assert downstream["state"] == EvidenceState.UNKNOWN.value
    assert artifacts["state"] == EvidenceState.UNKNOWN.value


def test_rejected_trigger_is_blocked():
    receipt = compose_workflow_evidence(observation(trigger=ObservationState.REJECTED, graph=ObservationState.UNKNOWN, created_jobs=None, completed_jobs=None))
    assert receipt["state"] == EvidenceState.BLOCKED.value
    assert receipt["production_claim_allowed"] is False


def test_invalid_counts_raise():
    with pytest.raises(ValueError, match="created_jobs cannot exceed expected_jobs"):
        compose_workflow_evidence(observation(created_jobs=4))
