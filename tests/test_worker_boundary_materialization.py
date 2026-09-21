"""Tests for pre-materialization worker boundary guards."""

import hashlib
from datetime import datetime, timezone
import pytest

from backend.execution.worker_boundary import WorkerResult, WorkerTaskValidator


def test_create_task_rejects_oversized_input_before_serialization():
    validator = WorkerTaskValidator()
    with pytest.raises(ValueError, match="task input"):
        validator.create_task(
            "fetch",
            {"content": "a" * (validator.MAX_OUTPUT_SIZE_MB * 1024 * 1024 + 1)},
            "run-1",
        )


def test_create_task_accepts_bounded_metadata():
    validator = WorkerTaskValidator()
    task = validator.create_task("fetch", {"url": "https://example.com"}, "run-1", {"m": 1})
    assert task.input_hash
    assert validator.validate_task(task)[0] is True


def test_validate_result_rejects_oversized_output_before_hashing():
    validator = WorkerTaskValidator()
    task = validator.create_task("fetch", {}, "run-1")
    validator.validate_task(task)
    output_data = {"content": "a" * (validator.MAX_OUTPUT_SIZE_MB * 1024 * 1024 + 1)}
    result = WorkerResult(
        task.task_id,
        task.nonce,
        "success",
        hashlib.sha256(b"unused").hexdigest(),
        output_data,
        1,
        "worker",
        datetime.now(timezone.utc),
    )
    ok, reason = validator.validate_result(task, result, output_data)
    assert ok is False
    assert "worker output" in reason
