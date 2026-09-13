"""Public-safe contracts for measurable planner strategies and token economics.

These models describe capabilities and decisions; they do not execute IO or own
provider/resource policy. Authority remains in the private Operations layer.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class StrategyFamily(str, Enum):
    QUERY = "query"
    ACQUISITION = "acquisition"
    PARSER = "parser"
    MAPPER = "mapper"
    VERIFIER = "verifier"
    SYNTHESIS = "synthesis"


class RetryDisposition(str, Enum):
    RETRY = "retry"
    ALTERNATE = "alternate"
    DEAD_LETTER = "dead_letter"
    STOP = "stop"


class TokenDecisionKind(str, Enum):
    ALLOW = "allow"
    CACHE = "cache"
    COMPRESS = "compress"
    DOWNGRADE = "downgrade"
    STOP = "stop"


@dataclass(frozen=True)
class RetryPolicy:
    max_attempts: int = 2
    base_delay_seconds: float = 1.0
    max_delay_seconds: float = 30.0
    multiplier: float = 2.0
    jitter_ratio: float = 0.10

    def validate(self) -> None:
        if self.max_attempts < 1:
            raise ValueError("max_attempts must be positive")
        if self.base_delay_seconds < 0:
            raise ValueError("base_delay_seconds must be non-negative")
        if self.max_delay_seconds < self.base_delay_seconds:
            raise ValueError("max_delay_seconds must be >= base_delay_seconds")
        if self.multiplier < 1:
            raise ValueError("multiplier must be >= 1")
        if not 0 <= self.jitter_ratio <= 1:
            raise ValueError("jitter_ratio must be in [0,1]")

    def delay_seconds(self, attempt: int) -> float:
        self.validate()
        if attempt < 1:
            raise ValueError("attempt must be positive")
        return min(self.max_delay_seconds, self.base_delay_seconds * (self.multiplier ** (attempt - 1)))


@dataclass(frozen=True)
class CacheProfile:
    exact: bool = True
    normalized: bool = True
    prefix_reusable: bool = False
    semantic: bool = False
    freshness_seconds: int | None = None

    def validate(self) -> None:
        if self.freshness_seconds is not None and self.freshness_seconds < 0:
            raise ValueError("freshness_seconds must be non-negative when provided")


@dataclass(frozen=True)
class TokenBudget:
    input_limit: int
    output_limit: int
    total_limit: int
    verification_reserve: int = 0
    final_answer_reserve: int = 0

    def validate(self) -> None:
        for name, value in (
            ("input_limit", self.input_limit),
            ("output_limit", self.output_limit),
            ("total_limit", self.total_limit),
            ("verification_reserve", self.verification_reserve),
            ("final_answer_reserve", self.final_answer_reserve),
        ):
            if value < 0:
                raise ValueError(f"{name} must be non-negative")
        if self.total_limit < self.input_limit + self.output_limit:
            raise ValueError("total_limit must cover input_limit + output_limit")
        if self.total_limit < self.verification_reserve + self.final_answer_reserve:
            raise ValueError("total_limit must cover reserved tokens")

    @property
    def usable_limit(self) -> int:
        self.validate()
        return self.total_limit - self.verification_reserve - self.final_answer_reserve


@dataclass(frozen=True)
class StrategyCard:
    strategy_id: str
    family: StrategyFamily
    owner: str
    expected_quality: float = 0.5
    expected_completeness: float = 0.5
    expected_latency_ms: float = 1000.0
    expected_resource_units: float = 1.0
    evidence_directness: float = 0.5
    risk_penalty: float = 0.0
    token_multiplier: float = 1.0
    cache: CacheProfile = CacheProfile()
    retry: RetryPolicy = RetryPolicy()

    def validate(self) -> None:
        if not self.strategy_id.strip():
            raise ValueError("strategy_id must not be empty")
        if not self.owner.strip():
            raise ValueError("owner must not be empty")
        for name, value in (
            ("expected_quality", self.expected_quality),
            ("expected_completeness", self.expected_completeness),
            ("evidence_directness", self.evidence_directness),
        ):
            if not 0 <= value <= 1:
                raise ValueError(f"{name} must be in [0,1]")
        if self.expected_latency_ms < 0:
            raise ValueError("expected_latency_ms must be non-negative")
        if self.expected_resource_units < 0:
            raise ValueError("expected_resource_units must be non-negative")
        if self.risk_penalty < 0:
            raise ValueError("risk_penalty must be non-negative")
        if self.token_multiplier <= 0:
            raise ValueError("token_multiplier must be positive")
        self.cache.validate()
        self.retry.validate()

    def utility(self) -> float:
        self.validate()
        return (
            self.expected_quality * 0.28
            + self.expected_completeness * 0.22
            + self.evidence_directness * 0.20
            - self.expected_latency_ms / 100000.0
            - self.expected_resource_units * 0.08
            - self.risk_penalty * 0.10
            + (0.05 if self.cache.exact else 0.0)
            + (0.03 if self.cache.prefix_reusable else 0.0)
        )


@dataclass(frozen=True)
class TokenDecision:
    kind: TokenDecisionKind
    estimated_tokens: int
    reason_code: str


def choose_token_decision(
    budget: TokenBudget,
    estimated_input: int,
    estimated_output: int,
    *,
    exact_cache_hit: bool = False,
    prefix_cache_hit: bool = False,
    compression_available: bool = False,
    downgrade_available: bool = False,
) -> TokenDecision:
    budget.validate()
    if estimated_input < 0 or estimated_output < 0:
        raise ValueError("estimated tokens must be non-negative")
    total = estimated_input + estimated_output
    if exact_cache_hit:
        return TokenDecision(TokenDecisionKind.CACHE, total, "exact_cache_hit")
    if total <= budget.usable_limit and estimated_input <= budget.input_limit and estimated_output <= budget.output_limit:
        return TokenDecision(TokenDecisionKind.ALLOW, total, "within_token_budget")
    if prefix_cache_hit and total <= budget.total_limit:
        return TokenDecision(TokenDecisionKind.CACHE, total, "prefix_cache_hit")
    if compression_available:
        return TokenDecision(TokenDecisionKind.COMPRESS, total, "budget_exceeded_compressible")
    if downgrade_available:
        return TokenDecision(TokenDecisionKind.DOWNGRADE, total, "budget_exceeded_downgrade")
    return TokenDecision(TokenDecisionKind.STOP, total, "token_budget_exhausted")


__all__ = [
    "CacheProfile",
    "RetryDisposition",
    "RetryPolicy",
    "StrategyCard",
    "StrategyFamily",
    "TokenBudget",
    "TokenDecision",
    "TokenDecisionKind",
    "choose_token_decision",
]
