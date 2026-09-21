"""Regression coverage for pre-materialization worker bounds."""

import hashlib
from datetime import datetime, timezone

import pytest

from backend.execution.worker_boundary import WorkerResult, WorkerTaskValidator


def test_oversized_input_is_rejected_before_json_materialization() -> None:
    validator = WorkerTaskValidator()
    with pytest.raises(ValueError, match="task input"):
        validator.create_task(
            "fetch",
            {"content": "a" * (validator.MAX_INPUT_SIZE_MB * 1024 * 1024 + 1)},
            "run-1",
        )


def test_bounded_metadata_remains_valid() -> None:
    validator = WorkerTaskValidator()
    task = validator.create_task("fetch", {"url": "https://example.com"}, "run-1", {"m": 1})
    assert task.input_hash
    assert validator.validate_task(task)[0] is True


def test_oversized_output_is_rejected_before_hashing() -> None:
    validator = WorkerTaskValidator()
    task = validator.create_task("fetch", {}, "run-1")
    validator.validate_task(task)
    payload = {"content": "x"}
    result = WorkerResult(
        task.task_id,
        task.nonce,
        "success",
        hashlib.sha256(b"unused").hexdigest(),
        {"content": "x"},
        1,
        "worker",
        datetime.now(timezone.utc),
    )
    original = validator.MAX_OUTPUT_SIZE_MB
    validator.MAX_OUTPUT_SIZE_MB = 0
    try:
        ok, reason = validator.validate_result(task, result, payload)
    finally:
        validator.MAX_OUTPUT_SIZE_MB = original
    assert ok is False
    assert "worker output" in reason
