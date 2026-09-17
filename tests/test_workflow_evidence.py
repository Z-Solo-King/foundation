import pytest
from backend.workflow_evidence import WorkflowEvidenceReceipt

def receipt(**overrides):
    values = dict(schema="workflow-evidence-receipt/v1", workflow="nightly", revision="abc", run_id="123", trigger_state="COMPLETE", graph_state="COMPLETE", job_count=2, job_state="COMPLETE", step_state="COMPLETE", artifact_state="COMPLETE", downstream_state="COMPLETE", diagnostic_state="COMPLETE")
    values.update(overrides)
    return WorkflowEvidenceReceipt(**values)

def test_success_is_complete(): assert receipt().aggregate_state == "COMPLETE"
def test_zero_job_is_unknown():
    value = receipt(job_count=0, graph_state="UNKNOWN", job_state="UNKNOWN", step_state="NOT_ATTEMPTED", artifact_state="NOT_ATTEMPTED", downstream_state="NOT_ATTEMPTED", diagnostic_state="UNKNOWN")
    assert value.aggregate_state == "UNKNOWN"
def test_partial_retains_partial_state():
    assert receipt(step_state="FAILED", downstream_state="NOT_ATTEMPTED").aggregate_state == "PARTIAL"
def test_zero_job_complete_is_rejected():
    with pytest.raises(ValueError, match="zero-job"): receipt(job_count=0, graph_state="UNKNOWN", job_state="COMPLETE")
def test_invalid_state_is_rejected():
    with pytest.raises(ValueError, match="invalid"): receipt(job_state="BROKEN")
