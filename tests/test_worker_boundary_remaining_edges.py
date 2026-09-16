import hashlib
import json
from datetime import datetime, timedelta, timezone


def test_worker_boundary_remaining_result_and_replay_guards():
    from backend.execution.worker_boundary import WorkerResult, WorkerTask, WorkerTaskValidator

    validator = WorkerTaskValidator()
    base = validator.create_task("fetch", {}, "p")
    assert validator.validate_task(WorkerTask("", base.nonce, base.schema_version, base.task_type, base.input_hash, base.provenance, base.created_at, base.expires_at, {}))[0] is False
    assert validator.validate_task(WorkerTask(base.task_id, base.nonce, "2.0", base.task_type, base.input_hash, base.provenance, base.created_at, base.expires_at, {}))[0] is False
    assert validator.validate_task(WorkerTask(base.task_id, base.nonce, base.schema_version, "unknown", base.input_hash, base.provenance, base.created_at, base.expires_at, {}))[0] is False

    huge = {"x": "a" * 17000}
    try:
        validator.create_task("fetch", {}, "p", huge)
    except ValueError as exc:
        assert "metadata exceeds" in str(exc)

    active = validator.create_task("fetch", {}, "p")
    assert validator.validate_task(active)[0] is True
    conflicting = WorkerTask(active.task_id + "2", active.nonce, active.schema_version, active.task_type, active.input_hash, active.provenance, active.created_at, active.expires_at, active.metadata)
    assert validator.validate_task(conflicting)[0] is False

    completed = validator.create_task("fetch", {}, "p")
    validator.validate_task(completed)
    validator._completed_nonces.add(completed.nonce)
    assert validator.validate_task(completed)[0] is False

    now = datetime.now(timezone.utc)
    good = validator.create_task("fetch", {"x": 1}, "p")
    for status in ("failure", "timeout", "invalid"):
        result = WorkerResult(good.task_id, good.nonce, status, None, None, 1, "worker", now)
        ok, reason = validator.validate_result(good, result, None)
        assert ok is True and reason == "valid"

    bad_status = WorkerResult(good.task_id, good.nonce, "bogus", None, None, 1, "worker", now)
    assert validator.validate_result(good, bad_status, None)[0] is False

    expired = validator.create_task("fetch", {}, "p")
    expired_task = WorkerTask(expired.task_id, expired.nonce, expired.schema_version, expired.task_type, expired.input_hash, expired.provenance, expired.created_at, now - timedelta(hours=2), expired.metadata)
    assert validator.validate_task(expired_task)[0] is False
    expired_result = WorkerResult(expired.task_id, expired.nonce, "failure", None, None, 1, "worker", now)
    assert validator.validate_result(expired_task, expired_result, None)[0] is False

    future = validator.create_task("fetch", {}, "p")
    future_result = WorkerResult(future.task_id, future.nonce, "failure", None, None, 1, "worker", now + timedelta(minutes=6))
    assert validator.validate_result(future, future_result, None)[0] is False

    missing_success = validator.create_task("fetch", {}, "p")
    missing_result = WorkerResult(missing_success.task_id, missing_success.nonce, "success", None, None, 1, "worker", now)
    ok, reason = validator.validate_result(missing_success, missing_result, None)
    assert ok is False and "output data" in reason

    monkeypatch_size = validator.MAX_OUTPUT_SIZE_MB
    validator.MAX_OUTPUT_SIZE_MB = 0
    oversized = validator.create_task("fetch", {}, "p")
    payload = {"x": 1}
    digest = hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode()).hexdigest()
    oversized_result = WorkerResult(oversized.task_id, oversized.nonce, "success", digest, payload, 1, "worker", now)
    ok, reason = validator.validate_result(oversized, oversized_result, payload)
    assert ok is False and "exceeds" in reason
    validator.MAX_OUTPUT_SIZE_MB = monkeypatch_size

    naive = WorkerResult(good.task_id, good.nonce, "failure", None, None, 1, "worker", now.replace(tzinfo=None))
    assert validator.validate_result(good, naive, None)[0] is False
    negative = WorkerResult(good.task_id, good.nonce, "failure", None, None, -1, "worker", now)
    assert validator.validate_result(good, negative, None)[0] is False
    missing_worker = WorkerResult(good.task_id, good.nonce, "failure", None, None, 1, "", now)
    assert validator.validate_result(good, missing_worker, None)[0] is False

    active._dummy = None
    validator._active_tasks[active.nonce] = "different-task"
    active_result = WorkerResult(active.task_id, active.nonce, "failure", None, None, 1, "worker", now)
    ok, reason = validator.validate_result(active, active_result, None)
    assert ok is False and "different task" in reason

    hashed = validator.create_task("fetch", {}, "p")
    bad_hash = hashlib.sha256(b"wrong").hexdigest()
    hashed_result = WorkerResult(hashed.task_id, hashed.nonce, "success", bad_hash, {"x": 1}, 1, "worker", now)
    ok, reason = validator.validate_result(hashed, hashed_result, {"x": 1})
    assert ok is False and "hash mismatch" in reason


def test_worker_boundary_concurrent_replay_guard():
    from backend.execution.worker_boundary import WorkerResult, WorkerTaskValidator

    validator = WorkerTaskValidator()
    task = validator.create_task("fetch", {}, "p")

    class RaceLock:
        def __enter__(self):
            validator._completed_nonces.add(task.nonce)
        def __exit__(self, *_):
            return False

    validator._completed_nonces.clear()
    validator._lock = RaceLock()
    assert validator.validate_task(task)[0] is False

    validator = WorkerTaskValidator()
    result_task = validator.create_task("fetch", {}, "p")
    validator._completed_nonces.add(result_task.nonce)
    result = WorkerResult(result_task.task_id, result_task.nonce, "failure", None, None, 1, "worker", datetime.now(timezone.utc))
    assert validator.validate_result(result_task, result, None)[0] is False
