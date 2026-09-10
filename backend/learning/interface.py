"""Public-safe learning interfaces.

This module carries proposal and measurement data only. Production promotion,
protected policy, and rollback authority live in the private control plane.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class BehaviorChangeProposal:
    change_id: str
    description: str
    affected_component: str


@dataclass(frozen=True)
class BehaviorEvaluation:
    change_id: str
    baseline_score: float
    candidate_score: float
    regression_rate: float
    improvement: float
    benchmark_count: int

    def as_dict(self) -> dict[str, object]:
        return {
            "change_id": self.change_id,
            "baseline_score": self.baseline_score,
            "candidate_score": self.candidate_score,
            "regression_rate": self.regression_rate,
            "improvement": self.improvement,
            "benchmark_count": self.benchmark_count,
        }
