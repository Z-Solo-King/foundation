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


def test_efficiency_is_unknown_without_resource_units():
    value = PerformanceSample("w", "p", "e", (), resource_units=0, completed_work_units=4)
    assert value.useful_completion_efficiency is None


def test_sample_validation_rejects_missing_identity_or_negative_values():
    with pytest.raises(ValueError, match="workload"):
        PerformanceSample("", "p", "e", ()).validate()
    with pytest.raises(ValueError, match="resource"):
        PerformanceSample("w", "p", "e", (), resource_units=-1).validate()
    with pytest.raises(ValueError, match="timing"):
        PerformanceSample("w", "p", "e", (), ttfb_ms=-1).validate()


def test_percentile_is_deterministic():
    assert percentile((10, 20, 30, 40), 50) == 25
    assert percentile((10, 20, 30, 40), 95) == 38.5
    assert percentile((10, 20, 30), 0) == 10
    assert percentile((10, 20, 30), 100) == 30


def test_percentile_rejects_empty_and_invalid_probability():
    with pytest.raises(ValueError, match="at least one"):
        percentile((), 95)
    with pytest.raises(ValueError, match="between"):
        percentile((10,), -1)
    with pytest.raises(ValueError, match="between"):
        percentile((10,), 101)


def test_regression_gate_uses_explicit_relative_threshold():
    threshold = RegressionThreshold("p95_time_to_final", 0.10)
    assert regression_allowed(baseline=100, candidate=105, threshold=threshold)
    assert not regression_allowed(baseline=100, candidate=111, threshold=threshold)


def test_regression_threshold_validates_metric_and_limit():
    with pytest.raises(ValueError, match="metric"):
        RegressionThreshold("", 0.1)
    with pytest.raises(ValueError, match="relative"):
        RegressionThreshold("metric", -0.1)


def test_regression_values_must_be_non_negative():
    threshold = RegressionThreshold("metric", 0.2)
    with pytest.raises(ValueError, match="negative"):
        regression_allowed(baseline=-1, candidate=0, threshold=threshold)
    with pytest.raises(ValueError, match="negative"):
        regression_allowed(baseline=1, candidate=-1, threshold=threshold)


def test_zero_baseline_is_not_divided_by_zero():
    threshold = RegressionThreshold("metric", 0.20)
    assert regression_allowed(baseline=0, candidate=0, threshold=threshold)
    assert not regression_allowed(baseline=0, candidate=1, threshold=threshold)


def test_invalid_samples_are_rejected():
    with pytest.raises(ValueError):
        StageTiming("", 1)
    with pytest.raises(ValueError):
        StageTiming("research", -1)



def test_performance_sample_rejects_missing_identity_fields_and_negative_budget():
    value = sample()
    for field in ("workload", "population", "environment"):
        payload = {
            "workload": value.workload,
            "population": value.population,
            "environment": value.environment,
            "stage_timings": value.stage_timings,
            "ttfb_ms": value.ttfb_ms,
            "time_to_evidence_ms": value.time_to_evidence_ms,
            "time_to_final_ms": value.time_to_final_ms,
            "resource_units": value.resource_units,
            "completed_work_units": value.completed_work_units,
        }
        payload[field] = " "
        with pytest.raises(ValueError):
            PerformanceSample(**payload).validate()
    with pytest.raises(ValueError):
        PerformanceSample(value.workload, value.population, value.environment, value.stage_timings, resource_units=-1).validate()
    with pytest.raises(ValueError):
        PerformanceSample(value.workload, value.population, value.environment, value.stage_timings, completed_work_units=-1).validate()


def test_performance_sample_rejects_negative_optional_timing():
    value = sample()
    with pytest.raises(ValueError):
        PerformanceSample(
            value.workload,
            value.population,
            value.environment,
            value.stage_timings,
            ttfb_ms=-1,
        ).validate()

# Protected-main check refresh: re-evaluate required checks against latest main.
