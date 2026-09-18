"""Reusable performance metrics and regression gates for deterministic benchmarking."""
from __future__ import annotations

from dataclasses import dataclass
from math import ceil


@dataclass(frozen=True)
class StageTiming:
    stage: str
    duration_ms: float

    def __post_init__(self) -> None:
        if not self.stage.strip():
            raise ValueError("stage must not be empty")
        if self.duration_ms < 0:
            raise ValueError("duration_ms must not be negative")


@dataclass(frozen=True)
class PerformanceSample:
    workload: str
    population: str
    environment: str
    stage_timings: tuple[StageTiming, ...]
    ttfb_ms: float | None = None
    time_to_evidence_ms: float | None = None
    time_to_final_ms: float | None = None
    resource_units: int = 0
    completed_work_units: int = 0

    def validate(self) -> None:
        if not self.workload.strip() or not self.population.strip() or not self.environment.strip():
            raise ValueError("workload, population and environment are required")
        if self.resource_units < 0 or self.completed_work_units < 0:
            raise ValueError("resource and completed-work units must not be negative")
        for value in (self.ttfb_ms, self.time_to_evidence_ms, self.time_to_final_ms):
            if value is not None and value < 0:
                raise ValueError("timing values must not be negative")

    @property
    def total_stage_ms(self) -> float:
        return sum(stage.duration_ms for stage in self.stage_timings)

    @property
    def useful_completion_efficiency(self) -> float | None:
        if self.resource_units <= 0:
            return None
        return self.completed_work_units / self.resource_units


def percentile(values: tuple[float, ...], p: float) -> float:
    if not values:
        raise ValueError("percentile requires at least one value")
    if not 0 <= p <= 100:
        raise ValueError("percentile must be between 0 and 100")
    ordered = sorted(values)
    rank = (len(ordered) - 1) * (p / 100)
    lower = int(rank)
    upper = ceil(rank)
    if lower == upper:
        return ordered[lower]
    weight = rank - lower
    return ordered[lower] + (ordered[upper] - ordered[lower]) * weight


@dataclass(frozen=True)
class RegressionThreshold:
    metric: str
    max_relative_regression: float

    def __post_init__(self) -> None:
        if not self.metric.strip():
            raise ValueError("metric must not be empty")
        if self.max_relative_regression < 0:
            raise ValueError("max_relative_regression must not be negative")


def regression_allowed(*, baseline: float, candidate: float, threshold: RegressionThreshold) -> bool:
    if baseline < 0 or candidate < 0:
        raise ValueError("metric values must not be negative")
    if baseline == 0:
        return candidate == 0
    return candidate <= baseline * (1 + threshold.max_relative_regression)


@dataclass(frozen=True)
class PerformanceGateResult:
    metric: str
    baseline: float
    candidate: float
    allowed: bool
    relative_change: float

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": "performance-gate/v1",
            "metric": self.metric,
            "baseline": self.baseline,
            "candidate": self.candidate,
            "allowed": self.allowed,
            "relative_change": self.relative_change,
        }


def evaluate_regression_gate(
    *,
    baseline: float,
    candidate: float,
    threshold: RegressionThreshold,
) -> PerformanceGateResult:
    allowed = regression_allowed(baseline=baseline, candidate=candidate, threshold=threshold)
    relative_change = 0.0 if baseline == 0 else (candidate - baseline) / baseline
    return PerformanceGateResult(
        metric=threshold.metric,
        baseline=baseline,
        candidate=candidate,
        allowed=allowed,
        relative_change=relative_change,
    )
