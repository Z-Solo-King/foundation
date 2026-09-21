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


def test_materialization_shape_covers_scalar_collections_and_budgets(monkeypatch):
    from backend.execution import worker_boundary as module

    module._validate_materialization_shape(
        [None, True, 7, 1.5, "ok", ("tuple",), {"k": "v"}],
        max_bytes=4096,
        field_name="payload",
    )

    value = 1
    for _ in range(module.MAX_MATERIALIZATION_DEPTH + 2):
        value = [value]
    with pytest.raises(ValueError, match="materialization depth"):
        module._validate_materialization_shape(value, max_bytes=4096, field_name="payload")

    monkeypatch.setattr(module, "MAX_MATERIALIZATION_ITEMS", 1)
    with pytest.raises(ValueError, match="item count"):
        module._validate_materialization_shape([1, 2], max_bytes=4096, field_name="payload")

    monkeypatch.setattr(module, "MAX_STRING_SIZE_BYTES", 1)
    with pytest.raises(ValueError, match="string exceeds"):
        module._validate_materialization_shape("too-long", max_bytes=4096, field_name="payload")


def test_materialization_shape_rejects_nonfinite_and_unsupported_keys_values():
    from backend.execution import worker_boundary as module

    with pytest.raises(ValueError, match="non-finite number"):
        module._validate_materialization_shape(float("nan"), max_bytes=4096, field_name="payload")
    with pytest.raises(ValueError, match="non-finite number key"):
        module._validate_materialization_shape({float("nan"): 1}, max_bytes=4096, field_name="payload")
    with pytest.raises(ValueError, match="unsupported JSON key type"):
        module._validate_materialization_shape({object(): 1}, max_bytes=4096, field_name="payload")
    with pytest.raises(ValueError, match="unsupported JSON value type"):
        module._validate_materialization_shape(object(), max_bytes=4096, field_name="payload")


def test_bounded_digest_enforces_encoded_size_and_reports_encoder_errors(monkeypatch):
    from backend.execution import worker_boundary as module

    with pytest.raises(ValueError, match="exceeds"):
        module._bounded_json_digest(123, max_bytes=1, field_name="payload", compact=False)
    with pytest.raises(ValueError, match="exceeds"):
        module._bounded_json_digest([1, 2], max_bytes=4, field_name="payload", compact=False)

    with pytest.raises(ValueError, match="exceeds"):
        module._bounded_json_digest({"text": "a\n"}, max_bytes=10, field_name="payload", compact=False)

    class BrokenEncoder:
        def __init__(self, **_kwargs):
            pass

        def iterencode(self, _value):
            raise TypeError("boom")

    monkeypatch.setattr(module.json, "JSONEncoder", BrokenEncoder)
    with pytest.raises(ValueError, match="not JSON serializable"):
        module._bounded_json_digest({"x": 1}, max_bytes=100, field_name="payload", compact=True)
