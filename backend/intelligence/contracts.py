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
    query_category: str | None = None
    required_source_families: tuple[str, ...] = ()

    def validate(self):
        if not self.question.strip():
            raise ValueError("question must not be empty")
        if self.max_sources < 1:
            raise ValueError("max_sources must be positive")
        if self.max_evidence_items < 1:
            raise ValueError("max_evidence_items must be positive")
        if any(not family.strip() for family in self.required_source_families):
            raise ValueError("required_source_families must contain non-empty names")
        if len(set(self.required_source_families)) != len(self.required_source_families):
            raise ValueError("required_source_families must not contain duplicates")


@dataclass(frozen=True)
class ResearchPlan:
    question: str
    stages: tuple[str, ...]
    source_budget: int
    evidence_budget: int
    metadata: dict[str, str] = field(default_factory=dict)
