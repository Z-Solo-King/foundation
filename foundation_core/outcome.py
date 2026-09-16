"""Canonical deterministic outcome taxonomy for resumable work.

The enum is intentionally provider- and framework-neutral. It describes the
meaning of a stage result, not how the stage was implemented.
"""
from __future__ import annotations

from enum import StrEnum


class StageOutcome(StrEnum):
    """Machine-readable outcome classes shared by execution stages."""

    COMPLETED = "completed"
    BLOCKED = "blocked"
    RETRYABLE_FAILURE = "retryable_failure"
    PERMANENT_FAILURE = "permanent_failure"
    INVALID_INPUT = "invalid_input"
    PARTIAL = "partial"
    EVIDENCE_INCOMPLETE = "evidence_incomplete"
    CANCELLED = "cancelled"


RETRYABLE_OUTCOMES = frozenset({StageOutcome.RETRYABLE_FAILURE})
TERMINAL_OUTCOMES = frozenset(
    {
        StageOutcome.COMPLETED,
        StageOutcome.BLOCKED,
        StageOutcome.PERMANENT_FAILURE,
        StageOutcome.INVALID_INPUT,
        StageOutcome.PARTIAL,
        StageOutcome.EVIDENCE_INCOMPLETE,
        StageOutcome.CANCELLED,
    }
)


def validate_outcome(value: str | StageOutcome) -> StageOutcome:
    """Normalize a stored outcome value and reject unknown states."""
    try:
        return value if isinstance(value, StageOutcome) else StageOutcome(value)
    except ValueError as exc:
        raise ValueError(f"unsupported stage outcome: {value!r}") from exc


def is_retryable(value: str | StageOutcome) -> bool:
    return validate_outcome(value) in RETRYABLE_OUTCOMES


def is_terminal(value: str | StageOutcome) -> bool:
    return validate_outcome(value) in TERMINAL_OUTCOMES
