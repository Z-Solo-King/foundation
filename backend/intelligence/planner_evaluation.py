"""Evaluation-only metrics for planner candidates.

Promotion authority remains outside Foundation's public planner.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


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


def candidate_improves(baseline: PlannerMetrics, candidate: PlannerMetrics,
                       floors: Mapping[str, float]) -> bool:
    if not safe_region(candidate, floors):
        return False
    quality = (candidate.task_coverage - baseline.task_coverage
               + candidate.claim_coverage - baseline.claim_coverage
               + candidate.retrieval_recall - baseline.retrieval_recall
               + candidate.citation_entailment - baseline.citation_entailment
               + candidate.primary_source_coverage - baseline.primary_source_coverage
               + candidate.independent_origin_coverage - baseline.independent_origin_coverage
               + candidate.contradiction_recall - baseline.contradiction_recall
               + candidate.freshness - baseline.freshness)
    efficiency = ((baseline.latency - candidate.latency)
                  + (baseline.resource_consumption - candidate.resource_consumption)
                  + (candidate.evidence_gain_per_unit - baseline.evidence_gain_per_unit))
    regret = candidate.research_regret <= baseline.research_regret
    return quality >= 0 and efficiency >= 0 and regret
