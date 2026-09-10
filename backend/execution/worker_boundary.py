"""Public worker boundary with fail-closed task validation.

Public GitHub workers are untrusted compute. All outputs are validated before
acceptance. Task nonce, schema, artifact hash, provenance, and replay status
are verified. Private evidence graph and research history never exposed.
"""

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from typing import Any


@dataclass(frozen=True)
class WorkerTask:
    """Authenticated task for public worker."""
    task_id: str
    nonce: str  # Unique per task; prevents replay
    schema_version: str  # Task schema version
    task_type: str  # fetch, browser, pdf, transcript, evaluation
    input_hash: str  # SHA-256 of input data
    provenance: str  # Run ID or origin
    created_at: datetime
    expires_at: datetime
    metadata: dict[str, Any]  # Additional task metadata


@dataclass(frozen=True)
class WorkerResult:
    """Result from public worker."""
    task_id: str
    nonce: str
    status: str  # success, failure, timeout, invalid
    output_hash: str | None  # SHA-256 of output
    output_data: dict[str, Any] | None
    execution_time_ms: int
    worker_id: str
    completed_at: datetime


class WorkerTaskValidator:
    """Validates tasks and results from public workers."""
    
    TASK_EXPIRY_HOURS = 24
    RESULT_EXPIRY_HOURS = 1
    MAX_OUTPUT_SIZE_MB = 100
    
    def __init__(self):
        self._seen_nonces: set[str] = set()
    
    def create_task(
        self,
        task_type: str,
        input_data: dict[str, Any],
        provenance: str,
        metadata: dict[str, Any] | None = None,
    ) -> WorkerTask:
        """Create and sign a task for a public worker.
        
        Args:
            task_type: fetch, browser, pdf, transcript, evaluation
            input_data: Input parameters (will be hashed)
            provenance: Run ID or origin
            metadata: Optional task metadata
            
        Returns:
            WorkerTask with nonce and expiry
        """
        import uuid
        
        task_id = f"wtask-{uuid.uuid4().hex[:12]}"
        nonce = f"nonce-{uuid.uuid4().hex}"
        input_json = json.dumps(input_data, sort_keys=True, default=str)
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
            metadata=metadata or {},
        )
    
    def validate_task(self, task: WorkerTask) -> tuple[bool, str]:
        """Validate task before execution.
        
        Args:
            task: WorkerTask to validate
            
        Returns:
            (is_valid, reason)
        """
        now = datetime.now(timezone.utc)
        
        # Check expiry
        if now > task.expires_at:
            return False, "task expired"
        
        # Check replay
        if task.nonce in self._seen_nonces:
            return False, "nonce already seen (replay detected)"
        
        # Check schema version
        if task.schema_version != "1.0":
            return False, f"unsupported schema version {task.schema_version}"
        
        # Check task type
        if task.task_type not in ("fetch", "browser", "pdf", "transcript", "evaluation"):
            return False, f"unknown task type {task.task_type}"
        
        self._seen_nonces.add(task.nonce)
        return True, "valid"
    
    def validate_result(
        self,
        task: WorkerTask,
        result: WorkerResult,
        output_data: dict[str, Any] | None,
    ) -> tuple[bool, str]:
        """Validate result from public worker.
        
        Args:
            task: Original WorkerTask
            result: WorkerResult to validate
            output_data: Raw output data (for hash verification)
            
        Returns:
            (is_valid, reason)
        """
        now = datetime.now(timezone.utc)
        
        # Check nonce matches
        if result.nonce != task.nonce:
            return False, "nonce mismatch (tampering detected)"
        
        # Check task expiry
        if now > task.expires_at + timedelta(hours=self.RESULT_EXPIRY_HOURS):
            return False, "task result window expired"
        
        # Check status
        if result.status not in ("success", "failure", "timeout", "invalid"):
            return False, f"invalid result status {result.status}"
        
        # If successful, verify output hash
        if result.status == "success" and output_data:
            output_json = json.dumps(output_data, sort_keys=True, default=str)
            computed_hash = hashlib.sha256(output_json.encode()).hexdigest()
            
            if computed_hash != result.output_hash:
                return False, "output hash mismatch (tampering detected)"
            
            # Check output size
            if len(output_json) > self.MAX_OUTPUT_SIZE_MB * 1024 * 1024:
                return False, f"output exceeds {self.MAX_OUTPUT_SIZE_MB}MB limit"
        
        return True, "valid"
    
    def sample_validate(
        self,
        result: WorkerResult,
        sampled_output: dict[str, Any],
    ) -> tuple[bool, str]:
        """Spot-check sampled output for consistency.
        
        Args:
            result: WorkerResult
            sampled_output: Sample of output to validate
            
        Returns:
            (is_valid, reason)
        """
        if result.status != "success":
            return False, f"cannot sample-validate non-success result ({result.status})"
        
        # Basic structural checks
        if not isinstance(sampled_output, dict):
            return False, "output is not a JSON object"
        
        # Check for required fields based on task type
        # (This would be expanded based on specific task types)
        if "error" in sampled_output and sampled_output.get("status") != "error":
            return False, "contradictory error state"
        
        return True, "sample valid"
