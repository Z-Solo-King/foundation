"""Deterministic scoring primitives for comparing model/agent runs.

This module is deliberately provider-neutral and observation-only. It never calls a
model provider and never treats model output as authoritative evidence.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Mapping


_SCORE_QUANTUM = Decimal("0.001")


def _score(value: float) -> float:
    """Clamp a score to [0, 1] and make serialized results stable."""
    return float(Decimal(str(max(0.0, min(1.0, value)))).quantize(_SCORE_QUANTUM, rounding=ROUND_HALF_UP))


def _ratio(numerator: int, denominator: int) -> float:
    if numerator < 0 or denominator < 0:
        raise ValueError("ratio inputs must be non-negative")
    if denominator == 0:
        return 0.0
    return _score(numerator / denominator)


@dataclass(frozen=True, slots=True)
class AgentRunObservation:
    """Provider-neutral observation of one agent run."""

    run_id: str
    provider: str
    model: str
    task_id: str
    input_tokens: int = 0
    output_tokens: int = 0
    cached_tokens: int = 0
    thinking_tokens: int = 0
    tool_calls: int = 0
    useful_tool_calls: int = 0
    relevant_sources: int = 0
    sources_used: int = 0
    files_read: int = 0
    duplicate_actions: int = 0
    irrelevant_actions: int = 0
    compaction_events: int = 0
    context_peak_tokens: int = 0
    required_claims: int = 0
    supported_claims: int = 0
    correct_claims: int = 0
    missed_requirements: int = 0
    unsupported_claims: int = 0
    self_corrections: int = 0
    successful_actions: int = 0

    def __post_init__(self) -> None:
        for name, value in asdict(self).items():
            if name in {"run_id", "provider", "model", "task_id"}:
                if not isinstance(value, str) or not value.strip():
                    raise ValueError(f"{name} must be a non-empty string")
                continue
            if not isinstance(value, int) or isinstance(value, bool) or value < 0:
                raise ValueError(f"{name} must be a non-negative integer")


@dataclass(frozen=True, slots=True)
class AgentBehaviorScore:
    run_id: str
    model: str
    task_id: str
    correctness: float
    evidence_quality: float
    completeness: float
    precision: float
    token_efficiency: float
    tool_efficiency: float
    context_efficiency: float
    self_correction: float
    overall: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def score_run(observation: AgentRunObservation) -> AgentBehaviorScore:
    """Score one observation using deterministic, auditable formulas."""
    correctness = _ratio(observation.correct_claims, observation.required_claims)
    evidence_quality = _ratio(observation.supported_claims, max(observation.correct_claims, observation.required_claims, 1))
    completeness = _score(1.0 - _ratio(observation.missed_requirements, max(observation.required_claims, 1)))

    action_count = max(observation.tool_calls + observation.files_read, 1)
    noise = observation.duplicate_actions + observation.irrelevant_actions + observation.unsupported_claims
    precision = _score(1.0 - min(1.0, noise / action_count))

    total_tokens = observation.input_tokens + observation.output_tokens + observation.thinking_tokens
    useful_signal = observation.correct_claims + observation.supported_claims + observation.self_corrections
    token_efficiency = _score(useful_signal / max(total_tokens / 1000.0, 1.0))

    tool_efficiency = _ratio(observation.useful_tool_calls, max(observation.tool_calls, 1))
    context_efficiency = _score(
        (observation.cached_tokens / max(total_tokens, 1)) * 0.35
        + (1.0 / (1 + observation.compaction_events)) * 0.35
        + (1.0 - min(1.0, observation.context_peak_tokens / max(total_tokens, 1))) * 0.30
    )
    self_correction = _score(
        observation.self_corrections / max(observation.successful_actions, observation.self_corrections, 1)
    )

    overall = _score(
        correctness * 0.24
        + evidence_quality * 0.18
        + completeness * 0.16
        + precision * 0.14
        + token_efficiency * 0.10
        + tool_efficiency * 0.06
        + context_efficiency * 0.07
        + self_correction * 0.05
    )
    return AgentBehaviorScore(
        run_id=observation.run_id,
        model=observation.model,
        task_id=observation.task_id,
        correctness=correctness,
        evidence_quality=evidence_quality,
        completeness=completeness,
        precision=precision,
        token_efficiency=token_efficiency,
        tool_efficiency=tool_efficiency,
        context_efficiency=context_efficiency,
        self_correction=self_correction,
        overall=overall,
    )


def compare_scores(scores: list[AgentBehaviorScore]) -> list[AgentBehaviorScore]:
    """Return scores ordered by overall score, then precision, then correctness."""
    return sorted(scores, key=lambda item: (item.overall, item.precision, item.correctness), reverse=True)


def compare_models(observations: list[AgentRunObservation]) -> dict[str, Any]:
    """Aggregate deterministic averages by model for cross-provider evaluation."""
    grouped: dict[str, list[AgentBehaviorScore]] = {}
    for observation in observations:
        grouped.setdefault(observation.model, []).append(score_run(observation))

    models: dict[str, dict[str, Any]] = {}
    metric_names = (
        "correctness",
        "evidence_quality",
        "completeness",
        "precision",
        "token_efficiency",
        "tool_efficiency",
        "context_efficiency",
        "self_correction",
        "overall",
    )
    for model, model_scores in grouped.items():
        aggregates = {
            metric: _score(sum(getattr(score, metric) for score in model_scores) / len(model_scores))
            for metric in metric_names
        }
        models[model] = {"runs": len(model_scores), "metrics": aggregates}
    return {"models": models}


def load_observation(payload: Mapping[str, Any]) -> AgentRunObservation:
    """Construct an observation from JSON-compatible input."""
    return AgentRunObservation(**dict(payload))
