"""Deterministic performance workloads for CI regression evidence.

This module defines reproducible synthetic workloads only. It does not claim
production/runtime measurements; it exercises the canonical performance
reporting and regression contracts with explicit workload, population and
environment identity.
"""

from __future__ import annotations

from dataclasses import dataclass

from backend.performance_metrics import PerformanceSample, StageTiming
from backend.performance_report import PerformanceReport, build_performance_report


REQUIRED_STAGES = (
    "queue",
    "routing",
    "authentication",
    "cache",
    "source_discovery",
    "parsing_normalization",
    "research",
    "model",
    "persistence",
    "serialization",
    "streaming_delivery",
)


@dataclass(frozen=True)
class PerformanceWorkload:
    name: str
    population: str
    environment: str
    concurrency: int
    research_scale: str
    samples: tuple[PerformanceSample, ...]

    def validate(self) -> None:
        if not self.name.strip() or not self.population.strip() or not self.environment.strip():
            raise ValueError("workload identity is required")
        if self.concurrency <= 0:
            raise ValueError("concurrency must be positive")
        if self.research_scale not in {"normal", "large"}:
            raise ValueError("research_scale must be normal or large")
        if not self.samples:
            raise ValueError("workload must contain samples")
        for sample in self.samples:
            sample.validate()


def _sample(
    *,
    workload: str,
    population: str,
    environment: str,
    multiplier: float,
    resource_units: int,
    completed_work_units: int,
) -> PerformanceSample:
    base = {
        "queue": 2.0,
        "routing": 3.0,
        "authentication": 2.0,
        "cache": 4.0,
        "source_discovery": 12.0,
        "parsing_normalization": 8.0,
        "research": 20.0,
        "model": 38.0,
        "persistence": 6.0,
        "serialization": 3.0,
        "streaming_delivery": 5.0,
    }
    return PerformanceSample(
        workload=workload,
        population=population,
        environment=environment,
        stage_timings=tuple(
            StageTiming(stage, duration * multiplier)
            for stage, duration in base.items()
        ),
        ttfb_ms=28.0 * multiplier,
        time_to_evidence_ms=64.0 * multiplier,
        time_to_final_ms=103.0 * multiplier,
        resource_units=resource_units,
        completed_work_units=completed_work_units,
    )


def deterministic_workloads() -> tuple[PerformanceWorkload, ...]:
    """Return normal-concurrency and large-research reproducible workloads."""
    workloads = (
        PerformanceWorkload(
            name="chat-concurrency-8",
            population="synthetic-chat-concurrency",
            environment="ci",
            concurrency=8,
            research_scale="normal",
            samples=tuple(
                _sample(
                    workload="chat-concurrency-8",
                    population="synthetic-chat-concurrency",
                    environment="ci",
                    multiplier=1.0 + (index * 0.01),
                    resource_units=10 + index,
                    completed_work_units=8 + index,
                )
                for index in range(8)
            ),
        ),
        PerformanceWorkload(
            name="large-research-evidence",
            population="synthetic-large-research",
            environment="ci",
            concurrency=4,
            research_scale="large",
            samples=tuple(
                _sample(
                    workload="large-research-evidence",
                    population="synthetic-large-research",
                    environment="ci",
                    multiplier=1.15 + (index * 0.015),
                    resource_units=24 + index,
                    completed_work_units=20 + index,
                )
                for index in range(12)
            ),
        ),
    )
    for workload in workloads:
        workload.validate()
        if any(
            {item.stage for item in sample.stage_timings} != set(REQUIRED_STAGES)
            for sample in workload.samples
        ):
            raise ValueError(f"{workload.name} is missing a required stage")
    return workloads


def build_workload_reports() -> tuple[PerformanceReport, ...]:
    return tuple(
        build_performance_report(workload.samples)
        for workload in deterministic_workloads()
    )


def render_ci_report() -> str:
    """Render deterministic benchmark output suitable for CI logs/summaries."""
    lines = [
        "# Performance workload report",
        "",
        "Synthetic, reproducible CI evidence; not production/runtime certification.",
        "",
    ]
    for report in build_workload_reports():
        lines.extend(
            [
                f"## {report.workload}",
                f"- population: {report.population}",
                f"- environment: {report.environment}",
                f"- samples: {report.sample_count}",
                f"- useful_completion_efficiency: {report.useful_completion_efficiency:.6f}",
            ]
        )
        for metric in report.stage_metrics:
            lines.append(
                f"- {metric.metric}: p50={metric.p50:.2f}ms "
                f"p95={metric.p95:.2f}ms p99={metric.p99:.2f}ms"
            )
        if report.ttfb is not None:
            lines.append(f"- ttfb_ms: p95={report.ttfb.p95:.2f}ms")
        if report.time_to_evidence is not None:
            lines.append(f"- time_to_evidence_ms: p95={report.time_to_evidence.p95:.2f}ms")
        if report.time_to_final is not None:
            lines.append(f"- time_to_final_ms: p95={report.time_to_final.p95:.2f}ms")
        lines.append("")
    return "\n".join(lines)


if __name__ == "__main__":
    print(render_ci_report())
