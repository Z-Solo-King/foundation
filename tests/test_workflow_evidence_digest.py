from backend.workflow_evidence import WorkflowEvidenceReceipt


def test_workflow_evidence_digest_is_deterministic():
    values = dict(schema="workflow-evidence-receipt/v1", workflow="nightly", revision="abc", run_id="1", trigger_state="COMPLETE", graph_state="COMPLETE", job_count=1, job_state="COMPLETE", step_state="COMPLETE", artifact_state="COMPLETE", downstream_state="COMPLETE", diagnostic_state="COMPLETE")
    assert WorkflowEvidenceReceipt(**values).digest() == WorkflowEvidenceReceipt(**values).digest()
