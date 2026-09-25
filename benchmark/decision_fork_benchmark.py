"""Deterministic, provider-neutral scoring for long-horizon decision forks.

The decision-maker must never receive the post-fork outcome. The harness records
that outcome separately and scores the observable choice after the trajectory
finishes. This isolates decision quality from final-task success.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Protocol, Sequence


@dataclass(frozen=True, slots=True)
class DecisionRequest:
    state: Mapping[str, Any]
    decision_type: str
    candidates: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class DecisionResult:
    chosen_candidate: str
    provider: str
    model: str
    latency_ms: float
    calls: int = 1


class DecisionProvider(Protocol):
    def decide(self, request: DecisionRequest) -> DecisionResult:
        ...


@dataclass(frozen=True, slots=True)
class DecisionForkObservation:
    run_id: str
    task_id: str
    trajectory_id: str
    fork_id: str
    state_digest: str
    decision_type: str
    candidates: tuple[str, ...]
    chosen_candidate: str
    hindsight_best_candidate: str
    outcome_visible_to_decider: bool
    provider: str
    model: str
    decision_latency_ms: float
    decision_calls: int = 1

    def __post_init__(self) -> None:
        text_fields = {
            "run_id": self.run_id,
            "task_id": self.task_id,
            "trajectory_id": self.trajectory_id,
            "fork_id": self.fork_id,
            "state_digest": self.state_digest,
            "decision_type": self.decision_type,
            "chosen_candidate": self.chosen_candidate,
            "hindsight_best_candidate": self.hindsight_best_candidate,
            "provider": self.provider,
            "model": self.model,
        }
        for name, value in text_fields.items():
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be a non-empty string")
        if len(self.candidates) < 2:
            raise ValueError("candidates must contain at least two options")
        if len(set(self.candidates)) != len(self.candidates):
            raise ValueError("candidates must be unique")
        if self.chosen_candidate not in self.candidates:
            raise ValueError("chosen_candidate must be one of candidates")
        if self.hindsight_best_candidate not in self.candidates:
            raise ValueError("hindsight_best_candidate must be one of candidates")
        if self.outcome_visible_to_decider:
            raise ValueError("post-fork outcome must be hidden from the decision-maker")
        if self.decision_latency_ms < 0:
            raise ValueError("decision_latency_ms must be non-negative")
        if self.decision_calls < 1:
            raise ValueError("decision_calls must be positive")


def score_decision_fork(observation: DecisionForkObservation) -> dict[str, Any]:
    """Return deterministic metrics for one fork."""
    correct = observation.chosen_candidate == observation.hindsight_best_candidate
    chosen_index = observation.candidates.index(observation.chosen_candidate)
    best_index = observation.candidates.index(observation.hindsight_best_candidate)
    normalized_rank_distance = abs(chosen_index - best_index) / max(len(observation.candidates) - 1, 1)
    return {
        "run_id": observation.run_id,
        "task_id": observation.task_id,
        "fork_id": observation.fork_id,
        "provider": observation.provider,
        "model": observation.model,
        "decision_correct": correct,
        "decision_accuracy": 1.0 if correct else 0.0,
        "normalized_rank_distance": round(normalized_rank_distance, 3),
        "decision_latency_ms": observation.decision_latency_ms,
        "decision_calls": observation.decision_calls,
    }


def aggregate_decision_forks(
    observations: Sequence[DecisionForkObservation],
) -> dict[str, Any]:
    """Aggregate without hiding the per-fork observations."""
    scored = [score_decision_fork(item) for item in observations]
    correct = sum(1 for item in scored if item["decision_correct"])
    latency = sum(item["decision_latency_ms"] for item in scored)
    distance = sum(item["normalized_rank_distance"] for item in scored)
    return {
        "schema": "decision-fork-report/v1",
        "observations": len(scored),
        "correct_observations": correct,
        "decision_accuracy": round(correct / len(scored), 3) if scored else 0.0,
        "mean_normalized_rank_distance": round(distance / len(scored), 3) if scored else 0.0,
        "mean_decision_latency_ms": round(latency / len(scored), 3) if scored else 0.0,
        "forks": scored,
    }


def load_decision_fork(payload: Mapping[str, Any]) -> DecisionForkObservation:
    """Load a JSON-compatible observation."""
    normalized = dict(payload)
    normalized["candidates"] = tuple(normalized["candidates"])
    return DecisionForkObservation(**normalized)
