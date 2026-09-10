from dataclasses import dataclass, field
from typing import Literal

ResearchDepth = Literal["quick", "standard", "deep"]


@dataclass(frozen=True)
class ResearchContract:
    question: str
    depth: ResearchDepth = "standard"
    require_citations: bool = True
    max_sources: int = 20
    max_evidence_items: int = 100

    def validate(self) -> None:
        if not self.question.strip():
            raise ValueError("question must not be empty")
        if self.max_sources < 1:
            raise ValueError("max_sources must be positive")
        if self.max_evidence_items < 1:
            raise ValueError("max_evidence_items must be positive")


@dataclass(frozen=True)
class ResearchPlan:
    question: str
    stages: tuple[str, ...]
    source_budget: int
    evidence_budget: int
    metadata: dict[str, str] = field(default_factory=dict)
