"""Pagination-completeness scaffold; not currently wired into the live execution path.

The tested receipt model is retained for planned/validated completeness semantics.
Production publication must continue to use the canonical active pipeline until
this primitive is deliberately integrated under existing authority boundaries.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class CompletenessStatus(StrEnum):
    COMPLETE = "complete"
    PARTIAL = "partial"
    BLOCKED = "blocked"
    UNAVAILABLE = "unavailable"
    UNKNOWN = "unknown"


class PaginationMode(StrEnum):
    PAGE_NUMBER = "page_number"
    CURSOR = "cursor"
    NEXT_LINK = "next_link"
    INFINITE_SCROLL = "infinite_scroll"


@dataclass(frozen=True)
class PageObservation:
    page_id: str
    sequence: int
    item_count: int
    next_token: str | None = None
    next_url: str | None = None
    status_code: int | None = None
    content_digest: str = ""

    def validate(self) -> None:
        if not self.page_id.strip():
            raise ValueError("page_id is required")
        if self.sequence < 1:
            raise ValueError("sequence must be positive")
        if self.item_count < 0:
            raise ValueError("item_count must be non-negative")
        if self.status_code is not None and not 100 <= self.status_code <= 599:
            raise ValueError("status_code must be a valid HTTP status")


@dataclass(frozen=True)
class CompletenessReceipt:
    schema: str
    mode: PaginationMode
    pages_visited: int
    items_observed: int
    termination_reason: str
    next_page_observed: bool
    completeness: CompletenessStatus
    blocked: bool
    replayable: bool

    @property
    def certified_complete(self) -> bool:
        return self.completeness == CompletenessStatus.COMPLETE


def certify_completeness(pages: tuple[PageObservation, ...], *, mode: PaginationMode | str, termination_reason: str, blocked: bool = False, unavailable: bool = False, replayable: bool = True) -> CompletenessReceipt:
    pagination_mode = PaginationMode(mode)
    if not termination_reason.strip():
        raise ValueError("termination_reason is required")
    if len({page.page_id for page in pages}) != len(pages):
        raise ValueError("duplicate page_id")
    if tuple(sorted(page.sequence for page in pages)) != tuple(range(1, len(pages) + 1)):
        raise ValueError("page sequences must be contiguous starting at 1")
    for page in pages:
        page.validate()
    next_seen = any(page.next_token or page.next_url for page in pages)
    if blocked:
        status = CompletenessStatus.BLOCKED
    elif unavailable:
        status = CompletenessStatus.UNAVAILABLE
    elif not pages:
        status = CompletenessStatus.UNKNOWN
    elif termination_reason in {"explicit_end", "no_next_page", "cursor_exhausted", "expected_total_reached"}:
        status = CompletenessStatus.COMPLETE
    elif termination_reason in {"repeated_page", "missing_next_link", "max_pages", "infinite_scroll_stopped"}:
        status = CompletenessStatus.PARTIAL
    else:
        status = CompletenessStatus.UNKNOWN
    return CompletenessReceipt("pagination-completeness-receipt/v1", pagination_mode, len(pages), sum(page.item_count for page in pages), termination_reason, next_seen, status, blocked, replayable)
