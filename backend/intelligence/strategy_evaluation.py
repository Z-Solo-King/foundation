"""Planner strategy experiment and lifecycle primitives.

These are evaluation records only; they cannot promote protected policy or mutate
production configuration. Protected Operations may consume a verified result.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
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


class StrategyStage(StrEnum):
    SHADOW = "shadow"
    CANARY = "canary"
    PROMOTABLE = "promotable"
    PROMOTED = "promoted"
    ROLLBACK = "rollback"


@dataclass(frozen=True)
class StrategyLifecycle:
    strategy_id: str
    version: str
    stage: StrategyStage = StrategyStage.SHADOW
    canary_fraction: float = 0.0
    last_experiment_id: str | None = None
    rollback_reason: str | None = None

    def validate(self) -> None:
        if not self.strategy_id.strip() or not self.version.strip():
            raise ValueError("strategy identity must not be empty")
        if not 0.0 <= self.canary_fraction <= 1.0:
            raise ValueError("canary_fraction must be between 0 and 1")
        if self.stage is StrategyStage.ROLLBACK and not (self.rollback_reason or "").strip():
            raise ValueError("rollback stage requires a reason")


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


def enter_canary(lifecycle: StrategyLifecycle, exp: StrategyExperiment, fraction: float) -> StrategyLifecycle:
    """Move an evaluated shadow strategy into bounded canary observation."""
    lifecycle.validate()
    if lifecycle.stage not in {StrategyStage.SHADOW, StrategyStage.PROMOTABLE}:
        raise ValueError("strategy must be shadow or promotable before canary")
    if not 0.0 < fraction <= 1.0:
        raise ValueError("canary fraction must be greater than zero and at most one")
    if not candidate_beats_baseline(exp):
        raise ValueError("strategy experiment is not eligible for canary")
    return StrategyLifecycle(lifecycle.strategy_id, lifecycle.version, StrategyStage.CANARY, fraction, exp.experiment_id)


def mark_promotable(lifecycle: StrategyLifecycle, exp: StrategyExperiment, floors: Mapping[str, float] | None = None) -> StrategyLifecycle:
    lifecycle.validate()
    if lifecycle.stage is not StrategyStage.CANARY:
        raise ValueError("only canary strategies can become promotable")
    if not candidate_beats_baseline(exp, floors):
        raise ValueError("canary experiment is not eligible for promotion")
    return StrategyLifecycle(lifecycle.strategy_id, lifecycle.version, StrategyStage.PROMOTABLE, lifecycle.canary_fraction, exp.experiment_id)


def mark_promoted(lifecycle: StrategyLifecycle) -> StrategyLifecycle:
    lifecycle.validate()
    if lifecycle.stage is not StrategyStage.PROMOTABLE:
        raise ValueError("only promotable strategies can enter promoted state")
    return StrategyLifecycle(lifecycle.strategy_id, lifecycle.version, StrategyStage.PROMOTED, 1.0, lifecycle.last_experiment_id)


def rollback(lifecycle: StrategyLifecycle, reason: str) -> StrategyLifecycle:
    lifecycle.validate()
    if not reason.strip():
        raise ValueError("rollback reason must not be empty")
    return StrategyLifecycle(lifecycle.strategy_id, lifecycle.version, StrategyStage.ROLLBACK, 0.0, lifecycle.last_experiment_id, reason)


__all__ = [
    "StrategyMetrics",
    "StrategyExperiment",
    "StrategyStage",
    "StrategyLifecycle",
    "candidate_beats_baseline",
    "enter_canary",
    "mark_promotable",
    "mark_promoted",
    "rollback",
]