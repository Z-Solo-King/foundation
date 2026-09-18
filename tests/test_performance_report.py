from backend.performance_metrics import PerformanceSample, StageTiming
from backend.performance_report import build_performance_report


def sample(
    *,
    ttfb_ms=None,
    time_to_evidence_ms=None,
    time_to_final_ms=None,
    resource_units=10,
    completed_work_units=8,
    stage_timings=None,
):
    return PerformanceSample(
        workload="research",
        population="benchmark-population",
        environment="ci",
        stage_timings=stage_timings or (
            StageTiming("retrieval", 10),
            StageTiming("model", 20),
        ),
        ttfb_ms=ttfb_ms,
        time_to_evidence_ms=time_to_evidence_ms,
        time_to_final_ms=time_to_final_ms,
        resource_units=resource_units,
        completed_work_units=completed_work_units,
    )


def test_performance_report_aggregates_stage_and_completion_metrics():
    report = build_performance_report(
        (
            sample(ttfb_ms=5, time_to_evidence_ms=15, time_to_final_ms=30),
            sample(ttfb_ms=7, time_to_evidence_ms=17, time_to_final_ms=34),
        )
    )

    assert report.sample_count == 2
    assert [item.metric for item in report.stage_metrics] == ["model", "retrieval"]
    assert report.ttfb is not None
    assert report.time_to_evidence is not None
    assert report.time_to_final is not None
    assert report.useful_completion_efficiency == 0.8
    assert report.to_dict()["schema_version"] == "performance-report/v1"


def test_performance_report_supports_missing_optional_metrics_and_zero_resources():
    report = build_performance_report(
        (
            sample(
                resource_units=0,
                completed_work_units=0,
                stage_timings=(StageTiming("model", 12),),
            ),
        )
    )

    assert report.ttfb is None
    assert report.time_to_evidence is None
    assert report.time_to_final is None
    assert report.useful_completion_efficiency is None


def test_performance_report_requires_samples_and_consistent_context():
    try:
        build_performance_report(())
    except ValueError as exc:
        assert "at least one" in str(exc)
    else:
        raise AssertionError("expected empty report rejection")

    try:
        build_performance_report(
            (
                sample(),
                PerformanceSample(
                    workload="other",
                    population="benchmark-population",
                    environment="ci",
                    stage_timings=(StageTiming("model", 20),),
                ),
            )
        )
    except ValueError as exc:
        assert "share workload" in str(exc)
    else:
        raise AssertionError("expected context mismatch rejection")


def test_performance_metric_summary_rejects_empty_values():
    from backend.performance_report import _summary

    try:
        _summary("latency", ())
    except ValueError as exc:
        assert "at least one value" in str(exc)
    else:
        raise AssertionError("expected empty metric rejection")
