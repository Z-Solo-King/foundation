"""Deterministic performance reporting for benchmark and CI evidence."""

from __future__ import annotations

from dataclasses import dataclass

from backend.performance_metrics import PerformanceSample, percentile


@dataclass(frozen=True)
class PerformanceMetricSummary:
    metric: str
    count: int
    p50: float
    p90: float
    p95: float
    p99: float

    def to_dict(self) -> dict[str, object]:
        return {
            "metric": self.metric,
            "count": self.count,
            "p50": self.p50,
            "p90": self.p90,
            "p95": self.p95,
            "p99": self.p99,
        }


@dataclass(frozen=True)
class PerformanceReport:
    workload: str
    population: str
    environment: str
    sample_count: int
    stage_metrics: tuple[PerformanceMetricSummary, ...]
    ttfb: PerformanceMetricSummary | None
    time_to_evidence: PerformanceMetricSummary | None
    time_to_final: PerformanceMetricSummary | None
    useful_completion_efficiency: float | None

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": "performance-report/v1",
            "workload": self.workload,
            "population": self.population,
            "environment": self.environment,
            "sample_count": self.sample_count,
            "stage_metrics": [item.to_dict() for item in self.stage_metrics],
            "ttfb": self.ttfb.to_dict() if self.ttfb else None,
            "time_to_evidence": self.time_to_evidence.to_dict() if self.time_to_evidence else None,
            "time_to_final": self.time_to_final.to_dict() if self.time_to_final else None,
            "useful_completion_efficiency": self.useful_completion_efficiency,
        }


def _summary(metric: str, values: tuple[float, ...]) -> PerformanceMetricSummary:
    if not values:
        raise ValueError("metric requires at least one value")
    return PerformanceMetricSummary(
        metric=metric,
        count=len(values),
        p50=percentile(values, 50),
        p90=percentile(values, 90),
        p95=percentile(values, 95),
        p99=percentile(values, 99),
    )


def _optional_summary(metric: str, values: tuple[float | None, ...]) -> PerformanceMetricSummary | None:
    present = tuple(value for value in values if value is not None)
    return None if not present else _summary(metric, tuple(present))


def build_performance_report(samples: tuple[PerformanceSample, ...]) -> PerformanceReport:
    if not samples:
        raise ValueError("performance report requires at least one sample")

    for sample in samples:
        sample.validate()

    first = samples[0]
    if any(
        (sample.workload, sample.population, sample.environment)
        != (first.workload, first.population, first.environment)
        for sample in samples[1:]
    ):
        raise ValueError("performance samples must share workload, population and environment")

    stage_values: dict[str, list[float]] = {}
    for sample in samples:
        for timing in sample.stage_timings:
            stage_values.setdefault(timing.stage, []).append(timing.duration_ms)

    stage_metrics = tuple(
        _summary(stage, tuple(stage_values[stage]))
        for stage in sorted(stage_values)
    )

    total_resources = sum(sample.resource_units for sample in samples)
    total_completed = sum(sample.completed_work_units for sample in samples)
    efficiency = None if total_resources == 0 else total_completed / total_resources

    return PerformanceReport(
        workload=first.workload,
        population=first.population,
        environment=first.environment,
        sample_count=len(samples),
        stage_metrics=stage_metrics,
        ttfb=_optional_summary("ttfb_ms", tuple(sample.ttfb_ms for sample in samples)),
        time_to_evidence=_optional_summary(
            "time_to_evidence_ms",
            tuple(sample.time_to_evidence_ms for sample in samples),
        ),
        time_to_final=_optional_summary(
            "time_to_final_ms",
            tuple(sample.time_to_final_ms for sample in samples),
        ),
        useful_completion_efficiency=efficiency,
    )
