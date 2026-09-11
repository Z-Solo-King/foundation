"""Public worker boundary with fail-closed task validation.

Public GitHub workers are untrusted compute. All outputs are validated before
acceptance. Task nonce, schema, task identity, artifact hash, provenance, and
replay status are verified. Private evidence graph and research history are
never exposed.
"""

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from threading import RLock
from typing import Any


@dataclass(frozen=True)
class WorkerTask:
    """Authenticated task for public worker."""
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
    """Result from public worker."""
    task_id: str
    nonce: str
    status: str
    output_hash: str | None
    output_data: dict[str, Any] | None
    execution_time_ms: int
    worker_id: str
    completed_at: datetime


class WorkerTaskValidator:
    """Validates tasks and results from public workers."""

    TASK_EXPIRY_HOURS = 24
    RESULT_EXPIRY_HOURS = 1
    MAX_OUTPUT_SIZE_MB = 100
    MAX_METADATA_SIZE_BYTES = 16 * 1024

    def __init__(self):
        self._lock = RLock()
        self._active_tasks: dict[str, str] = {}
        self._completed_nonces: set[str] = set()

    def create_task(
        self,
        task_type: str,
        input_data: dict[str, Any],
        provenance: str,
        metadata: dict[str, Any] | None = None,
    ) -> WorkerTask:
        """Create a task with a deterministic input digest and expiry."""
        import uuid

        if not task_type.strip():
            raise ValueError("task_type must not be empty")
        if not provenance.strip():
            raise ValueError("provenance must not be empty")
        task_id = f"wtask-{uuid.uuid4().hex[:12]}"
        nonce = f"nonce-{uuid.uuid4().hex}"
        input_json = json.dumps(input_data, sort_keys=True, default=str, separators=(",", ":"))
        metadata_value = metadata or {}
        metadata_json = json.dumps(metadata_value, sort_keys=True, default=str, separators=(",", ":"))
        if len(metadata_json.encode("utf-8")) > self.MAX_METADATA_SIZE_BYTES:
            raise ValueError("metadata exceeds size limit")
        input_hash = hashlib.sha256(input_json.encode()).hexdigest()
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(hours=self.TASK_EXPIRY_HOURS)

        return WorkerTask(
            task_id=task_id,
            nonce=nonce,
            schema_version="1.0",
            task_type=task_type,
            input_hash=input_hash,
            provenance=provenance,
            created_at=now,
            expires_at=expires_at,
            metadata=metadata_value,
        )

    def validate_task(self, task: WorkerTask) -> tuple[bool, str]:
        """Validate task before execution without consuming its nonce."""
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
        if task.task_type not in ("fetch", "browser", "pdf", "transcript", "evaluation"):
            return False, f"unknown task type {task.task_type}"
        metadata_json = json.dumps(task.metadata, sort_keys=True, default=str, separators=(",", ":"))
        if len(metadata_json.encode("utf-8")) > self.MAX_METADATA_SIZE_BYTES:
            return False, "task metadata exceeds size limit"

        with self._lock:
            if task.nonce in self._completed_nonces:
                return False, "nonce already completed (replay detected)"
            active_task_id = self._active_tasks.get(task.nonce)
            if active_task_id is not None and active_task_id != task.task_id:
                return False, "nonce already active for another task (replay detected)"
            self._active_tasks[task.nonce] = task.task_id
        return True, "valid"

    def validate_result(
        self,
        task: WorkerTask,
        result: WorkerResult,
        output_data: dict[str, Any] | None,
    ) -> tuple[bool, str]:
        """Validate and terminally consume a worker result."""
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
                output_json = json.dumps(output_data, sort_keys=True, default=str, separators=(",", ":"))
                computed_hash = hashlib.sha256(output_json.encode()).hexdigest()
                if computed_hash != result.output_hash:
                    return False, "output hash mismatch (tampering detected)"
                if len(output_json.encode("utf-8")) > self.MAX_OUTPUT_SIZE_MB * 1024 * 1024:
                    return False, f"output exceeds {self.MAX_OUTPUT_SIZE_MB}MB limit"

            self._active_tasks.pop(task.nonce, None)
            self._completed_nonces.add(task.nonce)
        return True, "valid"

    def sample_validate(
        self,
        result: WorkerResult,
        sampled_output: dict[str, Any],
    ) -> tuple[bool, str]:
        """Spot-check sampled output for consistency."""
        if result.status != "success":
            return False, f"cannot sample-validate non-success result ({result.status})"
        if not isinstance(sampled_output, dict):
            return False, "output is not a JSON object"
        if "error" in sampled_output and sampled_output.get("status") != "error":
            return False, "contradictory error state"
        return True, "sample valid"
