"""HTTP request/response models."""

from dataclasses import dataclass, field
from typing import Any, Literal


@dataclass(frozen=True)
class ResearchRequest:
    question: str
    depth: Literal["quick", "standard", "deep"] | None = None
    require_citations: bool = True
    max_sources: int = 20
    max_evidence_items: int = 100
    strict_zero_cost_only: bool = True
    source_urls: tuple[str, ...] = ()

    def validate(self) -> None:
        if not self.question.strip():
            raise ValueError("question required and must not be empty")
        if self.max_sources < 1 or self.max_evidence_items < 1:
            raise ValueError("budgets must be positive")
        if not self.strict_zero_cost_only:
            raise ValueError("strict $0 cost mode is mandatory: strict_zero_cost_only must be true")
        if len(self.source_urls) > self.max_sources:
            raise ValueError("source_urls exceeds max_sources")


@dataclass(frozen=True)
class ChatRequest:
    chat_id: str
    request_id: str
    message: str
    mode: Literal["chat"] = "chat"
    strict_zero_cost_only: bool = True
    metadata: dict[str, str] = field(default_factory=dict)

    def validate(self) -> None:
        if not self.chat_id.strip():
            raise ValueError("chat_id required and must not be empty")
        if not self.request_id.strip():
            raise ValueError("request_id required and must not be empty")
        if not self.message.strip():
            raise ValueError("message required and must not be empty")
        if len(self.message) > 16_384:
            raise ValueError("message exceeds the supported length")
        if self.mode != "chat":
            raise ValueError("Heroic AI public chat contract accepts mode=chat only")
        if not self.strict_zero_cost_only:
            raise ValueError("strict $0 cost mode is mandatory: strict_zero_cost_only must be true")
        if len(self.metadata) > 32:
            raise ValueError("metadata exceeds the supported field count")


@dataclass(frozen=True)
class APIResponse:
    ok: bool
    error: str | None = None
    run_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
