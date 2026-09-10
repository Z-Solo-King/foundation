"""Tests for worker boundary validation."""

import pytest
from datetime import datetime, timezone, timedelta

from backend.execution.worker_boundary import (
    WorkerTask,
    WorkerResult,
    WorkerTaskValidator,
)


def test_create_task():
    """Creating a task generates nonce and expiry."""
    validator = WorkerTaskValidator()
    task = validator.create_task(
        task_type="fetch",
        input_data={"url": "https://example.com"},
        provenance="run-1",
    )
    
    assert task.task_id.startswith("wtask-")
    assert task.nonce.startswith("nonce-")
    assert task.schema_version == "1.0"
    assert task.task_type == "fetch"
    assert task.expires_at > task.created_at


def test_validate_task_success():
    """Valid task passes validation."""
    validator = WorkerTaskValidator()
    task = validator.create_task(
        task_type="fetch",
        input_data={"url": "https://example.com"},
        provenance="run-1",
    )
    
    is_valid, reason = validator.validate_task(task)
    assert is_valid is True
    assert reason == "valid"


def test_validate_task_expired():
    """Expired task fails validation."""
    validator = WorkerTaskValidator()
    task = validator.create_task(
        task_type="fetch",
        input_data={"url": "https://example.com"},
        provenance="run-1",
    )
    
    # Manually expire the task
    expired_task = WorkerTask(
        task_id=task.task_id,
        nonce=task.nonce,
        schema_version=task.schema_version,
        task_type=task.task_type,
        input_hash=task.input_hash,
        provenance=task.provenance,
        created_at=task.created_at,
        expires_at=datetime.now(timezone.utc) - timedelta(hours=1),
        metadata=task.metadata,
    )
    
    is_valid, reason = validator.validate_task(expired_task)
    assert is_valid is False
    assert "expired" in reason


def test_validate_task_replay_detection():
    """Replay detection prevents nonce reuse."""
    validator = WorkerTaskValidator()
    task1 = validator.create_task(
        task_type="fetch",
        input_data={"url": "https://example.com"},
        provenance="run-1",
    )
    
    # Validate first task
    is_valid, reason = validator.validate_task(task1)
    assert is_valid is True
    
    # Create second task with same nonce (would-be replay)
    task2 = WorkerTask(
        task_id="wtask-other",
        nonce=task1.nonce,  # Same nonce
        schema_version=task1.schema_version,
        task_type=task1.task_type,
        input_hash=task1.input_hash,
        provenance="run-2",
        created_at=datetime.now(timezone.utc),
        expires_at=datetime.now(timezone.utc) + timedelta(hours=24),
        metadata={},
    )
    
    # Second validation should detect replay
    is_valid, reason = validator.validate_task(task2)
    assert is_valid is False
    assert "replay" in reason


def test_validate_result_success():
    """Valid result passes validation."""
    validator = WorkerTaskValidator()
    task = validator.create_task(
        task_type="fetch",
        input_data={"url": "https://example.com"},
        provenance="run-1",
    )
    
    # Validate task first
    validator.validate_task(task)
    
    # Create result
    output_data = {"status": "ok", "content": "test"}
    import json
    import hashlib
    output_json = json.dumps(output_data, sort_keys=True)
    output_hash = hashlib.sha256(output_json.encode()).hexdigest()
    
    result = WorkerResult(
        task_id=task.task_id,
        nonce=task.nonce,
        status="success",
        output_hash=output_hash,
        output_data=output_data,
        execution_time_ms=100,
        worker_id="worker-1",
        completed_at=datetime.now(timezone.utc),
    )
    
    is_valid, reason = validator.validate_result(task, result, output_data)
    assert is_valid is True


def test_validate_result_nonce_mismatch():
    """Result with mismatched nonce fails (tampering detected)."""
    validator = WorkerTaskValidator()
    task = validator.create_task(
        task_type="fetch",
        input_data={"url": "https://example.com"},
        provenance="run-1",
    )
    
    validator.validate_task(task)
    
    result = WorkerResult(
        task_id=task.task_id,
        nonce="wrong-nonce",  # Tampered nonce
        status="success",
        output_hash="xxx",
        output_data={},
        execution_time_ms=100,
        worker_id="worker-1",
        completed_at=datetime.now(timezone.utc),
    )
    
    is_valid, reason = validator.validate_result(task, result, {})
    assert is_valid is False
    assert "nonce mismatch" in reason
