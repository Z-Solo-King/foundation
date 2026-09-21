from datetime import datetime, timezone
import hashlib
import json
import pytest

from backend.execution.worker_boundary import WorkerResult, WorkerTaskValidator


def test_create_task_rejects_oversized_input_before_json_materialization():
    validator = WorkerTaskValidator()
    with pytest.raises(ValueError, match="task input"):
        validator.create_task(
            "fetch",
            {"content": "x" * (validator.MAX_OUTPUT_SIZE_MB * 1024 * 1024 + 1)},
            "run-1",
        )


def test_validate_result_rejects_oversized_output_before_hash_materialization():
    validator = WorkerTaskValidator()
    task = validator.create_task("fetch", {}, "run-1")
    validator.validate_task(task)
    output = {"content": "x" * (validator.MAX_OUTPUT_SIZE_MB * 1024 * 1024 + 1)}
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


def test_valid_output_hash_remains_compatible():
    validator = WorkerTaskValidator()
    task = validator.create_task("fetch", {}, "run-1")
    validator.validate_task(task)
    output = {"status": "ok", "content": "test"}
    digest = hashlib.sha256(json.dumps(output, sort_keys=True, default=str).encode()).hexdigest()
    result = WorkerResult(
        task.task_id,
        task.nonce,
        "success",
        digest,
        output,
        1,
        "worker",
        datetime.now(timezone.utc),
    )
    assert validator.validate_result(task, result, output) == (True, "valid")
