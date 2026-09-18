from backend.performance_metrics import RegressionThreshold, evaluate_regression_gate
from benchmark.performance_workloads import REQUIRED_STAGES, build_workload_reports, deterministic_workloads


def test_workloads_cover_concurrency_and_large_research():
    workloads = deterministic_workloads()
    assert {item.concurrency for item in workloads} == {8, 4}
    assert {item.research_scale for item in workloads} == {"normal", "large"}
    assert all(item.samples for item in workloads)


def test_reports_have_explicit_population_environment_and_stage_percentiles():
    reports = build_workload_reports()
    assert len(reports) == 2
    for report in reports:
        assert report.population
        assert report.environment == "ci"
        assert report.sample_count > 1
        assert {metric.metric for metric in report.stage_metrics} == set(REQUIRED_STAGES)
        assert all(metric.p50 <= metric.p95 <= metric.p99 for metric in report.stage_metrics)
        assert report.ttfb is not None
        assert report.time_to_evidence is not None
        assert report.time_to_final is not None
        assert report.useful_completion_efficiency is not None


def test_performance_regression_threshold_is_explicit():
    allowed = evaluate_regression_gate(
        baseline=100.0,
        candidate=108.0,
        threshold=RegressionThreshold("p95_latency_ms", 0.10),
    )
    blocked = evaluate_regression_gate(
        baseline=100.0,
        candidate=120.0,
        threshold=RegressionThreshold("p95_latency_ms", 0.10),
    )
    assert allowed.allowed is True
    assert blocked.allowed is False


def test_workload_output_is_reproducible():
    first = [report.to_dict() for report in build_workload_reports()]
    second = [report.to_dict() for report in build_workload_reports()]
    assert first == second
