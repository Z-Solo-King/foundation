import pytest

from foundation_core import (
    RETRYABLE_OUTCOMES,
    TERMINAL_OUTCOMES,
    StageOutcome,
    is_retryable,
    is_terminal,
    validate_outcome,
)


def test_all_declared_outcomes_are_classified():
    assert validate_outcome("completed") is StageOutcome.COMPLETED
    assert StageOutcome.RETRYABLE_FAILURE in RETRYABLE_OUTCOMES
    assert StageOutcome.BLOCKED in TERMINAL_OUTCOMES
    assert not is_retryable(StageOutcome.COMPLETED)
    assert is_retryable("retryable_failure")
    assert is_terminal("cancelled")


def test_retryable_failure_is_not_terminal():
    assert is_retryable(StageOutcome.RETRYABLE_FAILURE)
    assert not is_terminal(StageOutcome.RETRYABLE_FAILURE)


def test_unknown_outcome_fails_closed():
    with pytest.raises(ValueError, match="unsupported stage outcome"):
        validate_outcome("success")
