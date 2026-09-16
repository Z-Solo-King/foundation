"""Deterministic token-efficiency measurements and comparison gates."""
from __future__ import annotations

from dataclasses import dataclass
from math import isfinite


@dataclass(frozen=True)
class TokenEfficiencyObservation:
    planned_context_units: int
    retained_evidence_units: int
    dropped_evidence_units: int
    duplicate_evidence_dropped: int
    estimated_input_tokens: int
    estimated_output_tokens: int
    model_calls: int
    cache_hits: int = 0
    deterministic_steps: int = 0
    accepted: bool = False
    estimated_cached_input_tokens: int = 0

    def validate(self) -> None:
        for name, value in self.__dict__.items():
            if name != "accepted" and value < 0:
                raise ValueError(f"{name} must be non-negative")
        if self.retained_evidence_units + self.dropped_evidence_units > self.planned_context_units:
            raise ValueError("evidence units exceed planned context units")
        if self.estimated_cached_input_tokens > self.estimated_input_tokens:
            raise ValueError("cached input tokens cannot exceed input tokens")

    @property
    def evidence_retention_ratio(self) -> float:
        total = self.retained_evidence_units + self.dropped_evidence_units
        return 1.0 if total == 0 else self.retained_evidence_units / total

    @property
    def cache_hit_ratio(self) -> float:
        return self.cache_hits / max(1, self.model_calls)

    @property
    def cached_input_ratio(self) -> float:
        return self.estimated_cached_input_tokens / max(1, self.estimated_input_tokens)

    @property
    def total_estimated_tokens(self) -> int:
        return self.estimated_input_tokens + self.estimated_output_tokens

    @property
    def context_amplification_ratio(self) -> float:
        """Measure prompt+output tokens consumed per output token produced.

        A high cache-hit rate can still hide growing context. Tracking this
        ratio exposes that failure mode without claiming a quality judgment.
        """
        return self.total_estimated_tokens / max(1, self.estimated_output_tokens)

    def token_density(self) -> float:
        if not self.accepted or self.total_estimated_tokens == 0:
            return 0.0
        return 1.0 / self.total_estimated_tokens


@dataclass(frozen=True)
class EfficiencyGate:
    max_input_token_growth_ratio: float = 0.10
    max_total_token_growth_ratio: float = 0.10
    min_cache_hit_ratio: float = 0.0

    def validate(self) -> None:
        for name, value in (
            ("max_input_token_growth_ratio", self.max_input_token_growth_ratio),
            ("max_total_token_growth_ratio", self.max_total_token_growth_ratio),
            ("min_cache_hit_ratio", self.min_cache_hit_ratio),
        ):
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be between 0 and 1")


def compare_efficiency(
    baseline: TokenEfficiencyObservation,
    candidate: TokenEfficiencyObservation,
    *,
    gate: EfficiencyGate | None = None,
) -> tuple[bool, str]:
    baseline.validate()
    candidate.validate()
    gate = gate or EfficiencyGate()
    gate.validate()

    if candidate.accepted and not baseline.accepted:
        return True, "candidate is accepted while baseline is not"
    if not candidate.accepted:
        return False, "candidate is not accepted"
    if baseline.estimated_input_tokens <= 0 or baseline.total_estimated_tokens <= 0:
        return False, "baseline token measurements must be positive"

    input_growth = (candidate.estimated_input_tokens - baseline.estimated_input_tokens) / baseline.estimated_input_tokens
    total_growth = (candidate.total_estimated_tokens - baseline.total_estimated_tokens) / baseline.total_estimated_tokens
    if not isfinite(input_growth) or not isfinite(total_growth):
        return False, "token growth must be finite"
    if input_growth > gate.max_input_token_growth_ratio:
        return False, "candidate input-token growth exceeds gate"
    if total_growth > gate.max_total_token_growth_ratio:
        return False, "candidate total-token growth exceeds gate"
    if candidate.cache_hit_ratio < gate.min_cache_hit_ratio:
        return False, "candidate cache-hit ratio is below gate"
    if candidate.total_estimated_tokens <= baseline.total_estimated_tokens:
        return True, "candidate accepted with non-increasing token use"
    if candidate.evidence_retention_ratio > baseline.evidence_retention_ratio:
        return True, "candidate spends limited extra tokens for better evidence retention"
    return False, "candidate did not justify additional token use"
