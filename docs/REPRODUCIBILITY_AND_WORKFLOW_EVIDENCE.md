# Reproducibility and Workflow Execution Evidence

Foundation records reproducibility and workflow execution as evidence, not as inferred health.

## Reproducibility

`backend.reproducibility_receipt.ReproducibilityReceipt` binds a result to repository revision, workflow run, suite/configuration, provider mode, fixture identity/version, execution state, runtime class and execution time. The receipt digest is deterministic over canonical metadata and validation rejects tampering and invalid production claims.

A baseline is compatible only when repository, suite, configuration, provider mode, fixture and runtime class match. Revision and workflow run remain observable provenance fields and are not silently substituted.

## Workflow execution

`backend.workflow_evidence.WorkflowEvidenceReceipt` keeps trigger admission, graph admission, job creation, step execution, artifacts, downstream reachability and diagnostic availability separate. Zero-job runs cannot be represented as successful job or graph execution. Aggregate state preserves `UNKNOWN`, `BLOCKED`, `FAILED`, `PARTIAL` and `COMPLETE` semantics rather than treating missing execution as success.

These contracts provide repository-side evidence. They do not certify an external or production runtime without the corresponding L4/production evidence defined by the family evidence contract.
