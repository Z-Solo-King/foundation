"""Planner strategy experiment primitives.

These are evaluation records only; they cannot promote protected policy.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


@dataclass(frozen=True)
class StrategyMetrics:
    correctness: float
    evidence_quality: float
    citation_alignment: float
    independence: float
    freshness: float
    latency: float
    failure_rate: float
    resource_cost: float

    def safe(self, floors: Mapping[str, float]) -> bool:
        return all(getattr(self, key) >= floor for key, floor in floors.items())


@dataclass(frozen=True)
class StrategyExperiment:
    experiment_id: str
    baseline_id: str
    candidate_id: str
    corpus_fingerprint: str
    metrics: StrategyMetrics
    baseline_metrics: StrategyMetrics
    pre_registered: bool = True

    def improvement_vector(self) -> dict[str, float]:
        return {
            name: getattr(self.metrics, name) - getattr(self.baseline_metrics, name)
            for name in self.metrics.__dataclass_fields__
        }


def candidate_beats_baseline(exp: StrategyExperiment, floors: Mapping[str, float] | None = None) -> bool:
    if not exp.pre_registered:
        return False
    if floors and not exp.metrics.safe(floors):
        return False
    improvement = exp.improvement_vector()
    quality_ok = improvement["correctness"] >= 0 and improvement["evidence_quality"] >= 0
    trust_ok = improvement["citation_alignment"] >= 0 and improvement["independence"] >= 0
    efficiency_ok = improvement["latency"] <= 0 and improvement["resource_cost"] <= 0
    reliability_ok = improvement["failure_rate"] <= 0
    return quality_ok and trust_ok and efficiency_ok and reliability_ok
