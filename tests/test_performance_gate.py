from backend.performance_metrics import RegressionThreshold, evaluate_regression_gate


def test_performance_gate_is_explicit_and_serializable():
    result = evaluate_regression_gate(
        baseline=100,
        candidate=105,
        threshold=RegressionThreshold("latency_p95", 0.05),
    )
    assert result.allowed is True
    assert result.to_dict()["schema_version"] == "performance-gate/v1"


def test_performance_gate_blocks_quality_regression_over_threshold():
    result = evaluate_regression_gate(
        baseline=100,
        candidate=106,
        threshold=RegressionThreshold("latency_p95", 0.05),
    )
    assert result.allowed is False
