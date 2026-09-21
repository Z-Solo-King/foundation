"""Regression coverage for pre-materialization worker bounds."""

import hashlib
from datetime import datetime, timezone

import pytest

from backend.execution.worker_boundary import WorkerResult, WorkerTaskValidator


def test_task_input_budget_is_checked_before_json_encoding(monkeypatch):
    validator = WorkerTaskValidator()
    validator.MAX_INPUT_SIZE_MB = 0

    class ExplodingEncoder:
        def __init__(self, *args, **kwargs):
            raise AssertionError("JSON encoding must not run before the shape budget")

    import backend.execution.worker_boundary as worker_boundary
    monkeypatch.setattr(worker_boundary.json, "JSONEncoder", ExplodingEncoder)

    with pytest.raises(ValueError, match="task input"):
        validator.create_task("fetch", {"payload": "x"}, "run-1")


def test_success_output_budget_is_checked_before_full_materialization():
    validator = WorkerTaskValidator()
    task = validator.create_task("fetch", {}, "run-1")
    validator.validate_task(task)
    validator.MAX_OUTPUT_SIZE_MB = 0
    output = {"payload": "x"}
    result = WorkerResult(
        task.task_id,
        task.nonce,
        "success",
        hashlib.sha256(b"unused").hexdigest(),
        output,
        1,
        "worker",
        datetime.now(timezone.utc),
    )
    ok, reason = validator.validate_result(task, result, output)
    assert ok is False
    assert "worker output" in reason
