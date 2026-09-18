import pytest

from backend.performance_metrics import (
    PerformanceSample,
    RegressionThreshold,
    StageTiming,
    percentile,
    regression_allowed,
)


def sample():
    return PerformanceSample(
        workload="research-large",
        population="nightly",
        environment="ci",
        stage_timings=(
            StageTiming("routing", 10),
            StageTiming("research", 90),
            StageTiming("synthesis", 20),
        ),
        ttfb_ms=15,
        time_to_evidence_ms=95,
        time_to_final_ms=120,
        resource_units=10,
        completed_work_units=8,
    )


def test_stage_timings_and_useful_efficiency_are_explicit():
    value = sample()
    value.validate()
    assert value.total_stage_ms == 120
    assert value.useful_completion_efficiency == 0.8


def test_percentile_is_deterministic():
    assert percentile((10, 20, 30, 40), 50) == 25
    assert percentile((10, 20, 30, 40), 95) == 38.5


def test_regression_gate_uses_explicit_relative_threshold():
    threshold = RegressionThreshold("p95_time_to_final", 0.10)
    assert regression_allowed(baseline=100, candidate=105, threshold=threshold)
    assert not regression_allowed(baseline=100, candidate=111, threshold=threshold)


def test_zero_baseline_is_not_divided_by_zero():
    threshold = RegressionThreshold("metric", 0.20)
    assert regression_allowed(baseline=0, candidate=0, threshold=threshold)
    assert not regression_allowed(baseline=0, candidate=1, threshold=threshold)


def test_invalid_samples_are_rejected():
    with pytest.raises(ValueError):
        StageTiming("", 1)
    with pytest.raises(ValueError):
        StageTiming("research", -1)
    with pytest.raises(ValueError):
        percentile((), 95)
