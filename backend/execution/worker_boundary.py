"""Public worker task/result validation with bounded materialization."""

import hashlib
import json
import math
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from threading import RLock
from typing import Any

PUBLIC_TASK_TYPES = ("fetch", "browser", "pdf", "transcript")
MAX_INPUT_SIZE_BYTES = 100 * 1024 * 1024
MAX_OUTPUT_SIZE_BYTES = 100 * 1024 * 1024
MAX_METADATA_SIZE_BYTES = 16 * 1024
MAX_MATERIALIZATION_DEPTH = 32
MAX_MATERIALIZATION_ITEMS = 200_000
MAX_STRING_SIZE_BYTES = 8 * 1024 * 1024


def _validate_materialization_shape(value: Any, *, max_bytes: int, field_name: str) -> None:
    seen = 0

    def walk(current: Any, depth: int) -> int:
        nonlocal seen
        if depth > MAX_MATERIALIZATION_DEPTH:
            raise ValueError(f"{field_name} nesting exceeds materialization depth limit")
        seen += 1
        if seen > MAX_MATERIALIZATION_ITEMS:
            raise ValueError(f"{field_name} item count exceeds materialization limit")
        if current is None or isinstance(current, bool):
            return 4
        if isinstance(current, int):
            return len(str(current)) + 1
        if isinstance(current, float):
            if not math.isfinite(current):
                raise ValueError(f"{field_name} contains a non-finite number")
            return len(repr(current)) + 1
        if isinstance(current, str):
            size = len(current.encode("utf-8"))
            if size > MAX_STRING_SIZE_BYTES:
                raise ValueError(f"{field_name} string exceeds materialization limit")
            return size + 2
        if isinstance(current, (list, tuple)):
            total = 2
            for item in current:
                total += walk(item, depth + 1) + 1
                if total > max_bytes:
                    raise ValueError(f"{field_name} exceeds {max_bytes} byte materialization limit")
            return total
        if isinstance(current, dict):
            total = 2
            for key, item in current.items():
                if isinstance(key, float) and not math.isfinite(key):
                    raise ValueError(f"{field_name} contains a non-finite number key")
                if not isinstance(key, (str, int, float, bool)) and key is not None:
                    raise ValueError(f"{field_name} contains an unsupported JSON key type")
                total += walk(str(key), depth + 1) + walk(item, depth + 1) + 2
                if total > max_bytes:
                    raise ValueError(f"{field_name} exceeds {max_bytes} byte materialization limit")
            return total
        raise ValueError(f"{field_name} contains an unsupported JSON value type")

    if walk(value, 0) > max_bytes:
        raise ValueError(f"{field_name} exceeds {max_bytes} byte materialization limit")


def _bounded_json_digest(
    value: Any,
    *,
    max_bytes: int,
    field_name: str,
    compact: bool,
) -> str:
    _validate_materialization_shape(value, max_bytes=max_bytes, field_name=field_name)
    options: dict[str, Any] = {"sort_keys": True, "default": str, "ensure_ascii": False}
    if compact:
        options["separators"] = (",", ":")
    encoder = json.JSONEncoder(**options)
    digest = hashlib.sha256()
    total = 0
    try:
        for chunk in encoder.iterencode(value):
            encoded = chunk.encode("utf-8")
            total += len(encoded)
            if total > max_bytes:
                raise ValueError(f"{field_name} exceeds {max_bytes} byte materialization limit")
            digest.update(encoded)
    except (TypeError, ValueError) as exc:
        if "materialization limit" in str(exc):
            raise
        raise ValueError(f"{field_name} is not JSON serializable") from exc
    return digest.hexdigest()


@dataclass(frozen=True)
class WorkerTask:
    task_id: str
    nonce: str
    schema_version: str
    task_type: str
    input_hash: str
    provenance: str
    created_at: datetime
    expires_at: datetime
    metadata: dict[str, Any]


@dataclass(frozen=True)
class WorkerResult:
    task_id: str
    nonce: str
    status: str
    output_hash: str | None
    output_data: dict[str, Any] | None
    execution_time_ms: int
    worker_id: str
    completed_at: datetime


class WorkerTaskValidator:
    TASK_EXPIRY_HOURS = 24
    RESULT_EXPIRY_HOURS = 1
    MAX_INPUT_SIZE_MB = 100
    MAX_OUTPUT_SIZE_MB = 100
    MAX_METADATA_SIZE_BYTES = MAX_METADATA_SIZE_BYTES

    def __init__(self):
        self._lock = RLock()
        self._active_tasks: dict[str, str] = {}
        self._completed_nonces: set[str] = set()

    def create_task(self, task_type: str, input_data: dict[str, Any], provenance: str, metadata: dict[str, Any] | None = None) -> WorkerTask:
        import uuid

        if not task_type.strip():
            raise ValueError("task_type must not be empty")
        if not provenance.strip():
            raise ValueError("provenance must not be empty")

        task_id = f"wtask-{uuid.uuid4().hex[:12]}"
        nonce = f"nonce-{uuid.uuid4().hex}"
        input_hash = _bounded_json_digest(input_data, max_bytes=MAX_INPUT_SIZE_BYTES, field_name="task input", compact=True)
        metadata_value = metadata or {}
        _bounded_json_digest(metadata_value, max_bytes=MAX_METADATA_SIZE_BYTES, field_name="task metadata", compact=True)
        now = datetime.now(timezone.utc)
        return WorkerTask(
            task_id=task_id,
            nonce=nonce,
            schema_version="1.0",
            task_type=task_type,
            input_hash=input_hash,
            provenance=provenance,
            created_at=now,
            expires_at=now + timedelta(hours=self.TASK_EXPIRY_HOURS),
            metadata=metadata_value,
        )

    def validate_task(self, task: WorkerTask) -> tuple[bool, str]:
        now = datetime.now(timezone.utc)
        if not task.task_id or not task.nonce or not task.provenance:
            return False, "task identity and provenance are required"
        if now > task.expires_at:
            return False, "task expired"
        if task.expires_at < task.created_at:
            return False, "task expiry precedes creation"
        if task.nonce in self._completed_nonces:
            return False, "nonce already completed (replay detected)"
        if task.schema_version != "1.0":
            return False, f"unsupported schema version {task.schema_version}"
        if task.task_type not in PUBLIC_TASK_TYPES:
            return False, f"unknown public task type {task.task_type}"
        try:
            _bounded_json_digest(task.metadata, max_bytes=self.MAX_METADATA_SIZE_BYTES, field_name="task metadata", compact=True)
        except ValueError as exc:
            return False, str(exc)

        with self._lock:
            if task.nonce in self._completed_nonces:
                return False, "nonce already completed (replay detected)"
            active_task_id = self._active_tasks.get(task.nonce)
            if active_task_id is not None and active_task_id != task.task_id:
                return False, "nonce already active for another task (replay detected)"
            self._active_tasks[task.nonce] = task.task_id
        return True, "valid"

    def validate_result(self, task: WorkerTask, result: WorkerResult, output_data: dict[str, Any] | None) -> tuple[bool, str]:
        now = datetime.now(timezone.utc)
        if result.task_id != task.task_id:
            return False, "task ID mismatch (tampering detected)"
        if result.nonce != task.nonce:
            return False, "nonce mismatch (tampering detected)"
        if now > task.expires_at + timedelta(hours=self.RESULT_EXPIRY_HOURS):
            return False, "task result window expired"
        if result.completed_at.tzinfo is None or result.completed_at > now + timedelta(minutes=5):
            return False, "invalid completion timestamp"
        if result.execution_time_ms < 0:
            return False, "invalid execution time"
        if not result.worker_id.strip():
            return False, "worker_id is required"
        if result.status not in ("success", "failure", "timeout", "invalid"):
            return False, f"invalid result status {result.status}"

        with self._lock:
            if self._active_tasks.get(task.nonce) not in {None, task.task_id}:
                return False, "nonce is bound to a different task (tampering detected)"
            if task.nonce in self._completed_nonces:
                return False, "nonce already completed (replay detected)"
            if result.status == "success":
                if output_data is None or result.output_hash is None:
                    return False, "successful result requires output data and output hash"
                try:
                    computed_hash = _bounded_json_digest(
                        output_data,
                        max_bytes=self.MAX_OUTPUT_SIZE_MB * 1024 * 1024,
                        field_name="worker output",
                        compact=False,
                    )
                except ValueError as exc:
                    return False, str(exc)
                if computed_hash != result.output_hash:
                    return False, "output hash mismatch (tampering detected)"

            self._active_tasks.pop(task.nonce, None)
            self._completed_nonces.add(task.nonce)
        return True, "valid"

    def sample_validate(self, result: WorkerResult, sampled_output: dict[str, Any]) -> tuple[bool, str]:
        if result.status != "success":
            return False, f"cannot sample-validate non-success result ({result.status})"
        if not isinstance(sampled_output, dict):
            return False, "output is not a JSON object"
        if "error" in sampled_output and sampled_output.get("status") != "error":
            return False, "contradictory error state"
        return True, "sample valid"
