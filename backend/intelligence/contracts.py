from dataclasses import dataclass, field
from typing import Literal

from .planner_models import FieldRequirement, ResourceEnvelope

ResearchDepth = Literal["quick", "standard", "deep"]


@dataclass(frozen=True)
class ResearchContract:
    question: str
    depth: ResearchDepth = "standard"
    require_citations: bool = True
    max_sources: int = 20
    max_evidence_items: int = 100
    output_type: str = "answer"
    claims_required: tuple[str, ...] = ()
    field_requirements: tuple[FieldRequirement, ...] = ()
    freshness_requirement: int | None = None
    languages: tuple[str, ...] = ()
    source_families_required: tuple[str, ...] = ()
    primary_source_requirement: str = "preferred"
    community_evidence_requirement: str = "none"
    contradiction_requirement: str = "resolve"
    evidence_quality_floor: str = "standard"
    max_search_actions: int = 12
    max_browser_actions: int = 0
    max_ai_actions: int = 0
    max_wall_time: int = 300
    zero_cost_required: bool = True
    resource_envelope: ResourceEnvelope = field(default_factory=lambda: ResourceEnvelope(search_units=12, wall_seconds=300))

    def validate(self) -> None:
        if not self.question.strip():
            raise ValueError("question must not be empty")
        for name, value in (("max_sources", self.max_sources), ("max_evidence_items", self.max_evidence_items),
                            ("max_search_actions", self.max_search_actions), ("max_browser_actions", self.max_browser_actions),
                            ("max_ai_actions", self.max_ai_actions), ("max_wall_time", self.max_wall_time)):
            if value < 0:
                raise ValueError(f"{name} must be non-negative")
        if self.max_sources == 0:
            raise ValueError("max_sources must be positive")
        if self.max_evidence_items == 0:
            raise ValueError("max_evidence_items must be positive")
        if self.freshness_requirement is not None and self.freshness_requirement < 0:
            raise ValueError("freshness_requirement must be non-negative")
        seen: set[str] = set()
        for field_req in self.field_requirements:
            if not field_req.field_id.strip() or not field_req.semantic_name.strip():
                raise ValueError("field requirement identifiers must not be empty")
            if field_req.field_id in seen:
                raise ValueError(f"duplicate field requirement: {field_req.field_id}")
            seen.add(field_req.field_id)
        self.resource_envelope.validate()
        if self.max_search_actions > self.resource_envelope.search_units:
            raise ValueError("max_search_actions exceeds resource envelope")
        if self.max_wall_time and self.resource_envelope.wall_seconds and self.max_wall_time > self.resource_envelope.wall_seconds:
            raise ValueError("max_wall_time exceeds resource envelope")


@dataclass(frozen=True)
class ResearchPlan:
    question: str
    stages: tuple[str, ...]
    source_budget: int
    evidence_budget: int
    metadata: dict[str, str] = field(default_factory=dict)
