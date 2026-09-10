"""HTTP request/response models."""

from dataclasses import dataclass, field
from typing import Any, Literal


@dataclass(frozen=True)
class ResearchRequest:
    """POST /api/v1/research request payload."""
    question: str
    depth: Literal["quick", "standard", "deep"] | None = None
    require_citations: bool = True
    max_sources: int = 20
    max_evidence_items: int = 100
    strict_zero_cost_only: bool = True

    def validate(self) -> None:
        if not self.question.strip():
            raise ValueError("question required and must not be empty")
        if self.max_sources < 1 or self.max_evidence_items < 1:
            raise ValueError("budgets must be positive")
        if not self.strict_zero_cost_only:
            raise ValueError("strict $0 cost mode is mandatory: strict_zero_cost_only must be true")


@dataclass(frozen=True)
class APIResponse:
    """Standard API response envelope."""
    ok: bool
    error: str | None = None
    run_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
