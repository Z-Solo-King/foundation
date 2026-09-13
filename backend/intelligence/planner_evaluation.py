"""Evaluation-only metrics for planner candidates.

Promotion authority remains outside Foundation's public planner.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


QUALITY_METRICS = (
    "task_coverage",
    "claim_coverage",
    "retrieval_recall",
    "citation_entailment",
    "primary_source_coverage",
    "independent_origin_coverage",
    "contradiction_recall",
    "freshness",
)


@dataclass(frozen=True)
class PlannerMetrics:
    task_coverage: float = 0.0
    claim_coverage: float = 0.0
    retrieval_recall: float = 0.0
    citation_entailment: float = 0.0
    primary_source_coverage: float = 0.0
    independent_origin_coverage: float = 0.0
    contradiction_recall: float = 0.0
    freshness: float = 0.0
    research_regret: float = 0.0
    evidence_gain_per_unit: float = 0.0
    latency: float = 0.0
    resource_consumption: float = 0.0


def safe_region(metrics: PlannerMetrics, floors: Mapping[str, float], maximums: Mapping[str, float] | None = None) -> bool:
    if any(getattr(metrics, key) < value for key, value in floors.items()):
        return False
    if maximums and any(getattr(metrics, key) > value for key, value in maximums.items()):
        return False
    return True


def quality_non_regression(baseline: PlannerMetrics, candidate: PlannerMetrics, tolerance: float = 0.0) -> bool:
    return all(
        getattr(candidate, metric) + tolerance >= getattr(baseline, metric)
        for metric in QUALITY_METRICS
    )


def candidate_improves(baseline: PlannerMetrics, candidate: PlannerMetrics,
                       floors: Mapping[str, float]) -> bool:
    if not safe_region(candidate, floors):
        return False
    if not quality_non_regression(baseline, candidate):
        return False
    quality_gain = sum(getattr(candidate, metric) - getattr(baseline, metric) for metric in QUALITY_METRICS)
    efficiency_gain = (
        baseline.latency - candidate.latency
        + baseline.resource_consumption - candidate.resource_consumption
        + candidate.evidence_gain_per_unit - baseline.evidence_gain_per_unit
    )
    regret_ok = candidate.research_regret <= baseline.research_regret
    return (quality_gain > 0 or efficiency_gain > 0) and efficiency_gain >= 0 and regret_ok


__all__ = ["PlannerMetrics", "QUALITY_METRICS", "safe_region", "quality_non_regression", "candidate_improves"]
