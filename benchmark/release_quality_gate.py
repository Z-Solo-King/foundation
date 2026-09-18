"""Independent release-quality regression gate.

No aggregate score is produced. Every required dimension and performance gate is
checked independently, and any critical regression blocks the gate.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from benchmark.vector_scorecard import QualityDimension, VectorQualityScorecard
from backend.performance_metrics import PerformanceGateResult


class GateState(StrEnum):
    PASS = "pass"
    BLOCKED = "blocked"


@dataclass(frozen=True)
class QualityRegression:
    dimension: QualityDimension
    baseline: float
    candidate: float
    allowed_regression: float

    def to_dict(self) -> dict[str, object]:
        return {
            "dimension": self.dimension.value,
            "baseline": self.baseline,
            "candidate": self.candidate,
            "allowed_regression": self.allowed_regression,
        }


@dataclass(frozen=True)
class ReleaseQualityGate:
    state: GateState
    missing_dimensions: tuple[QualityDimension, ...]
    regressions: tuple[QualityRegression, ...]
    performance_failures: tuple[PerformanceGateResult, ...]
    workload: str
    population: str
    corpus_id: str
    corpus_version: str

    @property
    def allowed(self) -> bool:
        return self.state is GateState.PASS

    def to_dict(self) -> dict[str, object]:
        return {
            "schema": "release-quality-gate/v1",
            "state": self.state.value,
            "allowed": self.allowed,
            "workload": self.workload,
            "population": self.population,
            "corpus_id": self.corpus_id,
            "corpus_version": self.corpus_version,
            "missing_dimensions": [item.value for item in self.missing_dimensions],
            "regressions": [item.to_dict() for item in self.regressions],
            "performance_failures": [item.to_dict() for item in self.performance_failures],
            "aggregate_score": None,
            "rule": "every required dimension and performance gate is evaluated independently; critical regression blocks release",
        }


def _regressions(
    baseline: VectorQualityScorecard,
    candidate: VectorQualityScorecard,
) -> tuple[QualityRegression, ...]:
    baseline_by_dimension = {item.dimension: item for item in baseline.dimensions}
    result: list[QualityRegression] = []
    for item in candidate.dimensions:
        if not item.critical or item.value is None or item.max_regression is None:
            continue
        baseline_item = baseline_by_dimension.get(item.dimension)
        if baseline_item is None or baseline_item.value is None:
            continue
        if item.dimension is QualityDimension.LATENCY:
            degraded_by = item.value - baseline_item.value
        else:
            degraded_by = baseline_item.value - item.value
        if degraded_by > item.max_regression:
            result.append(
                QualityRegression(
                    item.dimension,
                    baseline_item.value,
                    item.value,
                    item.max_regression,
                )
            )
    return tuple(result)


def evaluate_release_quality(
    *,
    baseline: VectorQualityScorecard,
    candidate: VectorQualityScorecard,
    performance_failures: tuple[PerformanceGateResult, ...] = (),
) -> ReleaseQualityGate:
    baseline.validate()
    candidate.validate()

    if (
        baseline.workload != candidate.workload
        or baseline.population != candidate.population
        or baseline.corpus_id != candidate.corpus_id
        or baseline.corpus_version != candidate.corpus_version
    ):
        raise ValueError("baseline and candidate must share workload, population and corpus identity")

    missing = candidate.missing_dimensions()
    regressions = _regressions(baseline, candidate)
    failures = tuple(item for item in performance_failures if not item.allowed)
    state = GateState.PASS if not missing and not regressions and not failures else GateState.BLOCKED
    return ReleaseQualityGate(
        state=state,
        missing_dimensions=missing,
        regressions=regressions,
        performance_failures=failures,
        workload=candidate.workload,
        population=candidate.population,
        corpus_id=candidate.corpus_id,
        corpus_version=candidate.corpus_version,
    )
