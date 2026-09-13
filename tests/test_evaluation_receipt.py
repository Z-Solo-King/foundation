import math

import pytest

from backend.evaluation import EvaluationReceipt


def _receipt(**overrides):
    values = {
        "receipt_id": "eval-1",
        "candidate_fingerprint": "candidate",
        "baseline_fingerprint": "baseline",
        "corpus_fingerprint": "corpus",
        "oracle_fingerprint": "oracle",
        "suite_version": "suite-1",
        "benchmark_count": 50,
        "metrics": (("accuracy", 0.98), ("latency_ms", 100.0)),
        "passed": True,
        "created_at": "2026-09-13T00:00:00Z",
        "evaluator_version": "eval-1",
        "artifact_hash": "artifact",
    }
    values.update(overrides)
    return EvaluationReceipt(**values)


def test_receipt_is_stable_and_binds_inputs():
    first = _receipt()
    second = _receipt()
    assert first.fingerprint() == second.fingerprint()
    assert first.verify_binding(
        candidate_fingerprint="candidate",
        baseline_fingerprint="baseline",
        corpus_fingerprint="corpus",
        oracle_fingerprint="oracle",
        min_benchmark_count=50,
    )
    assert not first.verify_binding(
        candidate_fingerprint="other",
        baseline_fingerprint="baseline",
        corpus_fingerprint="corpus",
        oracle_fingerprint="oracle",
    )
    assert first.metric_map()["accuracy"] == 0.98


def test_receipt_rejects_invalid_identity_and_counts():
    with pytest.raises(ValueError):
        _receipt(receipt_id="").validate()
    with pytest.raises(ValueError):
        _receipt(benchmark_count=0).validate()
    with pytest.raises(ValueError):
        _receipt(metrics=()).validate()
    with pytest.raises(ValueError):
        _receipt(metrics=(("accuracy", 0.9), ("accuracy", 0.8))).validate()
    with pytest.raises(ValueError):
        _receipt(metrics=(("accuracy", math.nan),)).validate()
    with pytest.raises(ValueError):
        _receipt(metrics=(("accuracy", math.inf),)).validate()


def test_receipt_rejects_long_fields():
    for field in (
        "receipt_id",
        "candidate_fingerprint",
        "baseline_fingerprint",
        "corpus_fingerprint",
        "oracle_fingerprint",
        "suite_version",
        "created_at",
        "evaluator_version",
        "artifact_hash",
    ):
        with pytest.raises(ValueError):
            _receipt(**{field: "x" * 129}).validate()
    with pytest.raises(ValueError):
        _receipt(metrics=(("x" * 97, 1.0),)).validate()
