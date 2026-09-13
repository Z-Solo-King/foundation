"""Field-aware representation and pagination planning contracts."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Sequence

from .planner_models import PaginationKind


class Representation(str, Enum):
    API = "api"
    FEED = "feed"
    STRUCTURED = "structured"
    METADATA = "metadata"
    HTML = "html"
    BROWSER = "browser"
    IMAGE = "image"
    PDF_PAGE = "pdf_page"
    FRAME = "frame"
    TRANSCRIPT = "transcript"


@dataclass(frozen=True)
class FieldRequirement:
    field_id: str
    semantic_name: str
    required: bool = True
    exact: bool = False
    preferred_representations: tuple[Representation, ...] = ()
    allow_inference: bool = False
    source_families: tuple[str, ...] = ()


@dataclass(frozen=True)
class RepresentationRoute:
    representation: Representation
    supports_fields: tuple[str, ...]
    evidence_directness: float
    completeness: float
    estimated_cost: float
    policy_key: str | None = None


@dataclass(frozen=True)
class PaginationPlan:
    kind: PaginationKind
    page_size: int | None = None
    expected_total: int | None = None
    max_pages: int = 1
    detect_repeated_pages: bool = True
    detect_cursor_repetition: bool = True
    require_completeness: bool = False
    early_stop_reason: str | None = None

    def bounded(self) -> "PaginationPlan":
        pages = max(1, self.max_pages)
        if self.expected_total is not None and self.page_size and self.page_size > 0:
            pages = min(pages, max(1, (self.expected_total + self.page_size - 1) // self.page_size))
        return PaginationPlan(self.kind, self.page_size, self.expected_total, pages,
                              self.detect_repeated_pages, self.detect_cursor_repetition,
                              self.require_completeness, self.early_stop_reason)


def choose_routes(fields: Sequence[FieldRequirement], routes: Sequence[RepresentationRoute]) -> tuple[RepresentationRoute, ...]:
    required = {f.semantic_name for f in fields if f.required}
    scored: list[tuple[float, RepresentationRoute]] = []
    for route in routes:
        coverage = len(required.intersection(route.supports_fields)) / max(1, len(required))
        preferred = sum(1 for f in fields if route.representation in f.preferred_representations)
        score = coverage * 0.45 + route.evidence_directness * 0.25 + route.completeness * 0.20 + preferred * 0.05 - route.estimated_cost * 0.05
        scored.append((score, route))
    return tuple(r for _, r in sorted(scored, key=lambda x: (-x[0], x[1].representation.value)))
