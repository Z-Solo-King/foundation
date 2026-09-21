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


def test_materialization_guard_rejects_nested_nonfinite_and_unsupported_shapes(monkeypatch):
    import backend.execution.worker_boundary as wb

    with pytest.raises(ValueError, match="nesting"):
        wb._bounded_json_digest({"a": {"b": {"c": 1}}}, max_bytes=1024, field_name="payload") if False else None

    monkeypatch.setattr(wb, "MAX_MATERIALIZATION_DEPTH", 1)
    with pytest.raises(ValueError, match="nesting"):
        wb._bounded_json_digest({"a": {"b": 1}}, max_bytes=1024, field_name="payload")

    monkeypatch.setattr(wb, "MAX_MATERIALIZATION_DEPTH", 32)
    monkeypatch.setattr(wb, "MAX_MATERIALIZATION_ITEMS", 1)
    with pytest.raises(ValueError, match="item count"):
        wb._bounded_json_digest([1, 2], max_bytes=1024, field_name="payload")

    monkeypatch.setattr(wb, "MAX_MATERIALIZATION_ITEMS", 200_000)
    with pytest.raises(ValueError, match="non-finite"):
        wb._bounded_json_digest(float("inf"), max_bytes=1024, field_name="payload")
    with pytest.raises(ValueError, match="non-finite number key"):
        wb._bounded_json_digest({float("inf"): 1}, max_bytes=1024, field_name="payload")
    with pytest.raises(ValueError, match="unsupported JSON key type"):
        wb._bounded_json_digest({object(): 1}, max_bytes=1024, field_name="payload")
    with pytest.raises(ValueError, match="unsupported JSON value type"):
        wb._bounded_json_digest(object(), max_bytes=1024, field_name="payload")


def test_materialization_guard_rejects_string_and_recursive_size_limits(monkeypatch):
    import backend.execution.worker_boundary as wb

    monkeypatch.setattr(wb, "MAX_STRING_SIZE_BYTES", 1)
    with pytest.raises(ValueError, match="string exceeds"):
        wb._bounded_json_digest({"x": "ab"}, max_bytes=1024, field_name="payload")

    monkeypatch.setattr(wb, "MAX_STRING_SIZE_BYTES", 8 * 1024 * 1024)
    with pytest.raises(ValueError, match="exceeds 2 byte"):
        wb._bounded_json_digest([1, 2], max_bytes=2, field_name="payload")


def test_materialization_guard_hashes_list_and_dict_values():
    import backend.execution.worker_boundary as wb

    digest = wb._bounded_json_digest(
        {"items": [True, None, 3, 2.5, "ok"]},
        max_bytes=1024,
        field_name="payload",
        compact=True,
    )
    assert len(digest) == 64


def test_materialization_guard_enforces_encoder_chunk_budget(monkeypatch):
    import backend.execution.worker_boundary as wb

    class OversizeEncoder:
        def __init__(self, *args, **kwargs):
            pass

        def iterencode(self, value):
            yield "x" * 101

    monkeypatch.setattr(wb.json, "JSONEncoder", OversizeEncoder)
    with pytest.raises(ValueError, match="exceeds 100 byte"):
        wb._bounded_json_digest({"x": "ok"}, max_bytes=100, field_name="payload")
