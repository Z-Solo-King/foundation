"""Pure pagination/completeness planning state.

The planner describes pagination and termination expectations; acquisition executes them.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .planner_models import PaginationKind, StopReason


class PageObservation(str, Enum):
    PROGRESSED = "progressed"
    REPEATED = "repeated"
    EMPTY = "empty"
    PARTIAL = "partial"
    COMPLETE = "complete"
    ERROR = "error"


@dataclass(frozen=True)
class PaginationState:
    kind: PaginationKind
    pages_seen: int = 0
    items_seen: int = 0
    expected_total: int | None = None
    last_cursor: str | None = None
    seen_cursors: tuple[str, ...] = ()
    page_fingerprints: tuple[str, ...] = ()
    observation: PageObservation = PageObservation.PROGRESSED

    def observe(self, *, items: int, fingerprint: str | None = None, cursor: str | None = None,
                expected_total: int | None = None, partial: bool = False) -> "PaginationState":
        repeated_page = fingerprint is not None and fingerprint in self.page_fingerprints
        repeated_cursor = cursor is not None and cursor in self.seen_cursors
        new_pages = self.pages_seen + 1
        new_items = self.items_seen + max(0, items)
        total = expected_total if expected_total is not None else self.expected_total
        if repeated_page or repeated_cursor:
            status = PageObservation.REPEATED
        elif items == 0:
            status = PageObservation.EMPTY
        elif total is not None and new_items >= total:
            status = PageObservation.COMPLETE
        elif partial:
            status = PageObservation.PARTIAL
        else:
            status = PageObservation.PROGRESSED
        cursors = self.seen_cursors + ((cursor,) if cursor else ())
        fps = self.page_fingerprints + ((fingerprint,) if fingerprint else ())
        return PaginationState(self.kind, new_pages, new_items, total, cursor, cursors, fps, status)

    def stop_reason(self, max_pages: int, require_complete: bool = False) -> StopReason | None:
        if self.observation == PageObservation.REPEATED:
            return StopReason.LOW_INFORMATION_GAIN
        if self.observation == PageObservation.COMPLETE:
            return StopReason.QUALITY_FLOOR
        if self.pages_seen >= max_pages:
            return StopReason.BUDGET_EXHAUSTED if require_complete else StopReason.LOW_INFORMATION_GAIN
        return None
