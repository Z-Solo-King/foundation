import hashlib
import json
from datetime import datetime, timedelta, timezone
import pytest


def test_worker_boundary_fail_closed_all_branches():
    from backend.execution.worker_boundary import WorkerResult, WorkerTask, WorkerTaskValidator
    validator = WorkerTaskValidator()
    with pytest.raises(ValueError): validator.create_task("", {}, "p")
    with pytest.raises(ValueError): validator.create_task("fetch", {}, "")
    with pytest.raises(ValueError): validator.create_task("fetch", {}, "p", {"x":"a"*20000})
    task = validator.create_task("fetch", {"a":1}, "p", {"m":1})
    assert validator.validate_task(task)[0]
    expired = WorkerTask(task.task_id, task.nonce+"e", task.schema_version, task.task_type, task.input_hash, task.provenance, task.created_at, datetime.now(timezone.utc)-timedelta(hours=1), task.metadata)
    assert validator.validate_task(expired)[0] is False
    malformed = WorkerTask("", "", task.schema_version, task.task_type, task.input_hash, "", task.created_at, task.expires_at, task.metadata)
    assert "required" in validator.validate_task(malformed)[1]
    now = datetime.now(timezone.utc)
    backwards = WorkerTask(task.task_id, "nonce-b", task.schema_version, task.task_type, task.input_hash, task.provenance, now + timedelta(hours=2), now + timedelta(hours=1), task.metadata)
    assert "precedes" in validator.validate_task(backwards)[1]
    bad_schema = WorkerTask(task.task_id, "nonce-s", "2", task.task_type, task.input_hash, task.provenance, task.created_at, task.expires_at, task.metadata)
    assert validator.validate_task(bad_schema)[0] is False
    bad_type = WorkerTask(task.task_id, "nonce-t", task.schema_version, "x", task.input_hash, task.provenance, task.created_at, task.expires_at, task.metadata)
    assert validator.validate_task(bad_type)[0] is False
    huge_meta = WorkerTask(task.task_id, "nonce-m", task.schema_version, task.task_type, task.input_hash, task.provenance, task.created_at, task.expires_at, {"x":"a"*20000})
    assert validator.validate_task(huge_meta)[0] is False
    other = WorkerTask(task.task_id+"2", task.nonce, task.schema_version, task.task_type, task.input_hash, task.provenance, task.created_at, task.expires_at, task.metadata)
    assert "another task" in validator.validate_task(other)[1]
    def result(status="success", **kw):
        return WorkerResult(task.task_id, task.nonce, status, kw.get("output_hash"), kw.get("output_data"), kw.get("execution_time_ms", 1), kw.get("worker_id", "worker"), kw.get("completed_at", datetime.now(timezone.utc)))
    h = hashlib.sha256(b'{"x": 1}').hexdigest()
    assert validator.validate_result(task, result(output_hash=h), {"x":1})[0] is True
    task2 = validator.create_task("fetch", {}, "p")
    for r in (result("success", output_hash=h), WorkerResult("x", task2.nonce, "success", h, {"x":1}, 1, "worker", datetime.now(timezone.utc)), WorkerResult(task2.task_id, "bad", "success", h, {"x":1}, 1, "worker", datetime.now(timezone.utc)), WorkerResult(task2.task_id, task2.nonce, "weird", h, {"x":1}, 1, "worker", datetime.now(timezone.utc)), WorkerResult(task2.task_id, task2.nonce, "success", None, None, 1, "worker", datetime.now(timezone.utc)), WorkerResult(task2.task_id, task2.nonce, "success", "bad", {"x":1}, 1, "worker", datetime.now(timezone.utc)), WorkerResult(task2.task_id, task2.nonce, "success", h, {"x":1}, -1, "worker", datetime.now(timezone.utc)), WorkerResult(task2.task_id, task2.nonce, "success", h, {"x":1}, 1, "", datetime.now(timezone.utc)), WorkerResult(task2.task_id, task2.nonce, "success", h, {"x":1}, 1, "worker", datetime.now(timezone.utc)+timedelta(minutes=6))):
        validator.validate_result(task2, r, r.output_data)
    assert validator.sample_validate(result("failure"), {})[0] is False
    assert validator.sample_validate(result("success"), [1])[0] is False
    assert validator.sample_validate(result("success"), {"error":"x"})[0] is False
    assert validator.sample_validate(result("success"), {"error":"x","status":"error"})[0] is True


def test_worker_result_replay_and_size_guards():
    from backend.execution.worker_boundary import WorkerResult, WorkerTaskValidator
    validator = WorkerTaskValidator(); task = validator.create_task("fetch", {}, "p")
    output = {"x": 1}; digest = hashlib.sha256(json.dumps(output, sort_keys=True, default=str).encode()).hexdigest()
    result = WorkerResult(task.task_id, task.nonce, "success", digest, output, 1, "worker", datetime.now(timezone.utc))
    assert validator.validate_result(task, result, output)[0] is True
    assert validator.validate_task(task)[0] is False
    expired = validator.create_task("fetch", {}, "p")
    expired_result = WorkerResult(expired.task_id, expired.nonce, "failure", None, None, 1, "worker", expired.expires_at + timedelta(hours=3))
    assert validator.validate_result(expired, expired_result, None)[0] is False
    future = validator.create_task("fetch", {}, "p")
    future_result = WorkerResult(future.task_id, future.nonce, "failure", None, None, 1, "worker", datetime.now(timezone.utc) + timedelta(minutes=6))
    assert validator.validate_result(future, future_result, None)[0] is False
    oversized = validator.create_task("fetch", {}, "p")
    huge = {"x": "a" * (validator.MAX_OUTPUT_SIZE_MB * 1024 * 1024 + 1)}
    huge_hash = hashlib.sha256(json.dumps(huge, sort_keys=True, default=str).encode()).hexdigest()
    huge_result = WorkerResult(oversized.task_id, oversized.nonce, "success", huge_hash, huge, 1, "worker", datetime.now(timezone.utc))
    assert validator.validate_result(oversized, huge_result, huge)[0] is False


def test_worker_boundary_remaining_guards(monkeypatch):
    from backend.execution.worker_boundary import WorkerResult, WorkerTaskValidator
    validator = WorkerTaskValidator(); task = validator.create_task("fetch", {}, "p")
    now = datetime.now(timezone.utc)
    expired_task = task.__class__(task.task_id, task.nonce, task.schema_version, task.task_type, task.input_hash, task.provenance, task.created_at, now - timedelta(hours=2), task.metadata)
    ok, reason = validator.validate_result(expired_task, WorkerResult(task.task_id, task.nonce, "failure", None, None, 1, "worker", now), None)
    assert ok is False and "expired" in reason
    bad_order = task.__class__(task.task_id, task.nonce, task.schema_version, task.task_type, task.input_hash, task.provenance, now, now - timedelta(hours=1), task.metadata)
    assert validator.validate_task(bad_order)[0] is False
    future = validator.create_task("fetch", {}, "p")
    ok, reason = validator.validate_result(future, WorkerResult(future.task_id, future.nonce, "failure", None, None, 1, "worker", now + timedelta(minutes=6)), None)
    assert ok is False and "timestamp" in reason
    missing_success = validator.create_task("fetch", {}, "p")
    ok, reason = validator.validate_result(missing_success, WorkerResult(missing_success.task_id, missing_success.nonce, "success", None, None, 1, "worker", now), None)
    assert ok is False and "output data" in reason
    monkeypatch.setattr(validator, "MAX_OUTPUT_SIZE_MB", 0)
    oversized = validator.create_task("fetch", {}, "p"); payload = {"x": 1}; digest = hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode()).hexdigest()
    ok, reason = validator.validate_result(oversized, WorkerResult(oversized.task_id, oversized.nonce, "success", digest, payload, 1, "worker", now), payload)
    assert ok is False and "exceeds" in reason
    assert validator.sample_validate(WorkerResult("t", "n", "failure", None, None, 1, "w", now), {})[0] is False
    assert validator.sample_validate(WorkerResult("t", "n", "success", "h", {}, 1, "w", now), {"error": "x"})[0] is False


def test_worker_task_and_result_validation_all_remaining_rejections(monkeypatch):
    from backend.execution.worker_boundary import WorkerTask, WorkerResult, WorkerTaskValidator
    validator = WorkerTaskValidator(); base = validator.create_task("fetch", {}, "p")
    assert validator.validate_task(WorkerTask("", base.nonce, base.schema_version, base.task_type, base.input_hash, base.provenance, base.created_at, base.expires_at, {}))[0] is False
    assert validator.validate_task(WorkerTask(base.task_id, base.nonce, "2.0", base.task_type, base.input_hash, base.provenance, base.created_at, base.expires_at, {}))[0] is False
    assert validator.validate_task(WorkerTask(base.task_id, base.nonce, base.schema_version, "unknown", base.input_hash, base.provenance, base.created_at, base.expires_at, {}))[0] is False
    with pytest.raises(ValueError, match="metadata exceeds"): validator.create_task("fetch", {}, "p", {"x":"a"*17000})
    active = validator.create_task("fetch", {}, "p"); assert validator.validate_task(active)[0] is True
    conflicting = WorkerTask(active.task_id+"2", active.nonce, active.schema_version, active.task_type, active.input_hash, active.provenance, active.created_at, active.expires_at, active.metadata)
    assert validator.validate_task(conflicting)[0] is False
    completed = validator.create_task("fetch", {}, "p"); validator.validate_task(completed); validator._completed_nonces.add(completed.nonce); assert validator.validate_task(completed)[0] is False
    expired = WorkerTask(base.task_id+"x", "nonce-expired", base.schema_version, base.task_type, base.input_hash, base.provenance, base.created_at, datetime.now(timezone.utc)-timedelta(hours=1), base.metadata); assert validator.validate_task(expired)[0] is False
    good = validator.create_task("fetch", {"x":1}, "p"); now = datetime.now(timezone.utc)
    assert validator.validate_result(good, WorkerResult(good.task_id, good.nonce, "bogus", None, None, 1, "worker", now), None)[0] is False
    for status in ("failure", "timeout", "invalid"):
        task = validator.create_task("fetch", {status:1}, "p"); ok, reason = validator.validate_result(task, WorkerResult(task.task_id, task.nonce, status, None, None, 1, "worker", now), None); assert ok is True and reason == "valid"


def test_worker_concurrent_replay_guards():
    from backend.execution.worker_boundary import WorkerTaskValidator, WorkerResult
    validator = WorkerTaskValidator(); task = validator.create_task("fetch", {}, "p")
    class RaceLock:
        def __enter__(self): validator._completed_nonces.add(task.nonce)
        def __exit__(self, *_): return False
    validator._completed_nonces.clear(); validator._lock = RaceLock(); assert validator.validate_task(task)[0] is False
    validator = WorkerTaskValidator(); result_task = validator.create_task("fetch", {}, "p"); validator._completed_nonces.add(result_task.nonce)
    result = WorkerResult(result_task.task_id, result_task.nonce, "failure", None, None, 1, "worker", datetime.now(timezone.utc)); assert validator.validate_result(result_task, result, None)[0] is False


def test_worker_result_rejects_invalid_timestamp_and_execution_time():
    from backend.execution.worker_boundary import WorkerResult, WorkerTaskValidator
    validator = WorkerTaskValidator(); task = validator.create_task("fetch", {}, "p"); now = datetime.now(timezone.utc)
    assert validator.validate_result(task, WorkerResult(task.task_id, task.nonce, "failure", None, None, 1, "worker", now.replace(tzinfo=None)), None)[0] is False
    assert validator.validate_result(task, WorkerResult(task.task_id, task.nonce, "failure", None, None, 1, "worker", now + timedelta(minutes=6)), None)[0] is False
    assert validator.validate_result(task, WorkerResult(task.task_id, task.nonce, "failure", None, None, -1, "worker", now), None)[0] is False
    assert validator.validate_result(task, WorkerResult(task.task_id, task.nonce, "failure", None, None, 1, "", now), None)[0] is False


def test_worker_boundary_remaining_result_guards():
    from backend.execution.worker_boundary import WorkerResult, WorkerTaskValidator
    validator = WorkerTaskValidator(); task = validator.create_task("fetch", {}, "p"); now = datetime.now(timezone.utc)
    for status, execution_time, worker_id in (("success", -1, "worker"), ("success", 1, ""), ("bogus", 1, "worker")):
        ok, _ = validator.validate_result(task, WorkerResult(task.task_id, task.nonce, status, None, None, execution_time, worker_id, now), None); assert ok is False
    active = validator.create_task("fetch", {}, "p"); validator._active_tasks[active.nonce] = "different-task"
    ok, reason = validator.validate_result(active, WorkerResult(active.task_id, active.nonce, "failure", None, None, 1, "worker", now), None); assert ok is False and "different task" in reason
    hashed = validator.create_task("fetch", {}, "p"); payload = {"x":1}; bad_hash = hashlib.sha256(b"wrong").hexdigest()
    ok, reason = validator.validate_result(hashed, WorkerResult(hashed.task_id, hashed.nonce, "success", bad_hash, payload, 1, "worker", now), payload); assert ok is False and "hash mismatch" in reason
