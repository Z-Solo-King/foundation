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


def test_unknown_trigger_and_graph_admission_are_unknown():
    trigger = compose_workflow_evidence(observation(trigger=ObservationState.UNKNOWN, graph=ObservationState.ADMITTED, created_jobs=None, completed_jobs=None))
    graph = compose_workflow_evidence(observation(graph=ObservationState.UNKNOWN, created_jobs=None, completed_jobs=None))
    not_admitted = compose_workflow_evidence(observation(graph=ObservationState.NOT_ADMITTED, created_jobs=None, completed_jobs=None))
    assert trigger["state"] == EvidenceState.UNKNOWN.value
    assert graph["state"] == EvidenceState.UNKNOWN.value
    assert not_admitted["state"] == EvidenceState.BLOCKED.value


def test_partial_job_creation_preserves_partial_state():
    receipt = compose_workflow_evidence(observation(created_jobs=2, completed_jobs=2))
    assert receipt["state"] == EvidenceState.PARTIAL.value
    assert "fewer jobs" in receipt["reason"]


def test_expected_zero_and_unobserved_job_creation_are_unknown():
    no_expected_jobs = compose_workflow_evidence(observation(expected_jobs=0, created_jobs=0, completed_jobs=0))
    not_observed = compose_workflow_evidence(observation(created_jobs=None, completed_jobs=None))
    assert no_expected_jobs["state"] == EvidenceState.UNKNOWN.value
    assert not_observed["state"] == EvidenceState.UNKNOWN.value


def test_failed_job_is_failed_not_complete():
    receipt = compose_workflow_evidence(observation(completed_jobs=2, failed_jobs=1))
    assert receipt["state"] == EvidenceState.FAILED.value
    assert receipt["production_claim_allowed"] is False


def test_cancelled_or_skipped_job_is_partial():
    cancelled = compose_workflow_evidence(observation(completed_jobs=2, cancelled_jobs=1))
    skipped = compose_workflow_evidence(observation(completed_jobs=2, skipped_jobs=1))
    assert cancelled["state"] == EvidenceState.PARTIAL.value
    assert skipped["state"] == EvidenceState.PARTIAL.value


def test_incomplete_completed_count_is_partial():
    receipt = compose_workflow_evidence(observation(completed_jobs=2))
    assert receipt["state"] == EvidenceState.PARTIAL.value
    assert "not all expected jobs" in receipt["reason"]


def test_downstream_states_are_preserved():
    not_reached = compose_workflow_evidence(observation(downstream=ObservationState.NOT_REACHED))
    unknown = compose_workflow_evidence(observation(downstream=ObservationState.UNKNOWN))
    assert not_reached["state"] == EvidenceState.PARTIAL.value
    assert unknown["state"] == EvidenceState.UNKNOWN.value


def test_artifact_and_diagnostics_states_are_preserved():
    artifact_unknown = compose_workflow_evidence(observation(artifacts=ObservationState.UNKNOWN))
    artifact_unavailable = compose_workflow_evidence(observation(artifacts=ObservationState.UNAVAILABLE))
    artifact_not_reached = compose_workflow_evidence(observation(artifacts=ObservationState.NOT_REACHED))
    diagnostics_unknown = compose_workflow_evidence(observation(diagnostics=ObservationState.UNKNOWN))
    diagnostics_unavailable = compose_workflow_evidence(observation(diagnostics=ObservationState.UNAVAILABLE))
    assert artifact_unknown["state"] == EvidenceState.UNKNOWN.value
    assert artifact_unavailable["state"] == EvidenceState.UNKNOWN.value
    assert artifact_not_reached["state"] == EvidenceState.PARTIAL.value
    assert diagnostics_unknown["state"] == EvidenceState.UNKNOWN.value
    assert diagnostics_unavailable["state"] == EvidenceState.UNKNOWN.value


def test_rejected_trigger_is_blocked():
    receipt = compose_workflow_evidence(observation(trigger=ObservationState.REJECTED, graph=ObservationState.UNKNOWN, created_jobs=None, completed_jobs=None))
    assert receipt["state"] == EvidenceState.BLOCKED.value
    assert receipt["production_claim_allowed"] is False


@pytest.mark.parametrize(
    ("changes", "message"),
    [
        ({"created_jobs": -1}, "job counts cannot be negative"),
        ({"created_jobs": 4}, "created_jobs cannot exceed expected_jobs"),
        ({"created_jobs": 2, "completed_jobs": 3}, "completed_jobs cannot exceed created_jobs"),
        ({"created_jobs": 2, "failed_jobs": 3}, "failed_jobs cannot exceed created_jobs"),
    ],
)
def test_invalid_counts_raise(changes, message):
    with pytest.raises(ValueError, match=message):
        compose_workflow_evidence(observation(**changes))
