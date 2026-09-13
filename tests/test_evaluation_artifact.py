from dataclasses import replace

import pytest

from backend.evaluation.artifact import EvaluationInputSnapshot, create_evaluation_artifact, verify_evaluation_artifact
from backend.evaluation.receipt import EvaluationReceipt


def make_inputs():
    return EvaluationInputSnapshot(
        contract_fingerprint="contract",
        plan_fingerprint="plan",
        candidate_fingerprint="candidate",
        baseline_fingerprint="baseline",
        capability_version="cap-v1",
        policy_version="policy-v1",
        source_profile_version="source-v1",
        corpus_fingerprint="corpus",
        oracle_fingerprint="oracle",
        benchmark_ids=("case-1", "case-2"),
        created_at="2026-09-13T17:00:00Z",
    )


def make_receipt():
    return EvaluationReceipt(
        receipt_id="receipt",
        candidate_fingerprint="candidate",
        baseline_fingerprint="baseline",
        corpus_fingerprint="corpus",
        oracle_fingerprint="oracle",
        suite_version="suite-1",
        benchmark_count=2,
        metrics=(("correctness", 1.0), ("efficiency", 0.8)),
        passed=True,
        created_at="2026-09-13T17:01:00Z",
        evaluator_version="eval-v1",
        artifact_hash="artifact-hash",
    )


def test_evaluation_artifact_binds_inputs_receipt_and_result():
    inputs = make_inputs()
    artifact = create_evaluation_artifact(inputs, make_receipt(), result_payload={"case-1": True, "case-2": True})
    assert artifact.inputs.fingerprint()
    assert artifact.fingerprint()
    assert verify_evaluation_artifact(
        artifact,
        expected_input_fingerprint=inputs.fingerprint(),
        expected_candidate_fingerprint="candidate",
    )
    assert not verify_evaluation_artifact(
        artifact,
        expected_input_fingerprint="wrong",
        expected_candidate_fingerprint="candidate",
    )


def test_input_snapshot_rejects_missing_or_duplicate_benchmark_ids():
    with pytest.raises(ValueError):
        replace(make_inputs(), benchmark_ids=()).validate()
    with pytest.raises(ValueError):
        replace(make_inputs(), benchmark_ids=("case-1", "case-1")).validate()
    with pytest.raises(ValueError):
        replace(make_inputs(), benchmark_ids=("case-1", "")).validate()
    with pytest.raises(ValueError):
        replace(make_inputs(), candidate_fingerprint="").validate()


def test_artifact_rejects_receipt_count_or_binding_drift():
    inputs = make_inputs()
    receipt = make_receipt()
    with pytest.raises(ValueError):
        create_evaluation_artifact(inputs, replace(receipt, benchmark_count=1), result_payload={})
    with pytest.raises(ValueError):
        create_evaluation_artifact(inputs, replace(receipt, candidate_fingerprint="other"), result_payload={})
    with pytest.raises(ValueError):
        artifact = create_evaluation_artifact(inputs, receipt, result_payload={})
        replace(artifact, result_fingerprint="").validate()