"""Public contracts for sandboxed code execution.

This module intentionally does not execute code. Uploading code never implies execution;
protected execution adapters must supply an approved sandbox identity and enforce their own
platform/security policy before running a request.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class CodeExecutionStatus(StrEnum):
    NOT_REQUESTED = "not_requested"
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    REJECTED = "rejected"
    TIMED_OUT = "timed_out"
    CANCELLED = "cancelled"


@dataclass(frozen=True)
class CodeExecutionPolicy:
    sandbox_required: bool = True
    network_allowed: bool = False
    max_runtime_seconds: int = 30
    max_output_bytes: int = 1_000_000
    max_memory_bytes: int = 256_000_000
    allow_subprocess: bool = False

    def validate(self) -> None:
        if not isinstance(self.sandbox_required, bool) or not self.sandbox_required:
            raise ValueError("code execution must require a sandbox")
        for name in ("max_runtime_seconds", "max_output_bytes", "max_memory_bytes"):
            if getattr(self, name) <= 0:
                raise ValueError(f"{name} must be positive")


@dataclass(frozen=True)
class CodeExecutionRequest:
    request_id: str
    artifact_ref: str
    artifact_hash: str
    language: str
    entrypoint: str
    sandbox_ref: str | None = None
    policy: CodeExecutionPolicy = CodeExecutionPolicy()
    requested_network: bool = False

    def validate(self) -> None:
        for name in ("request_id", "artifact_ref", "artifact_hash", "language", "entrypoint"):
            if not getattr(self, name).strip():
                raise ValueError(f"{name} must not be empty")
        if len(self.artifact_hash) != 64:
            raise ValueError("artifact_hash must be a SHA-256 hex digest")
        self.policy.validate()
        if self.requested_network and not self.policy.network_allowed:
            raise ValueError("request requests network access outside declared policy")
        if self.sandbox_ref is None or not self.sandbox_ref.strip():
            raise ValueError("sandbox_ref is required; upload alone cannot trigger execution")


@dataclass(frozen=True)
class CodeExecutionResult:
    request_id: str
    status: CodeExecutionStatus
    exit_code: int | None = None
    stdout_ref: str | None = None
    stderr_ref: str | None = None
    stdout_bytes: int = 0
    stderr_bytes: int = 0
    runtime_seconds: float = 0.0
    sandbox_ref: str | None = None
    result_hash: str | None = None
    failure_reason: str | None = None

    def validate(self) -> None:
        if not self.request_id.strip():
            raise ValueError("request_id must not be empty")
        for name in ("stdout_bytes", "stderr_bytes"):
            if getattr(self, name) < 0:
                raise ValueError(f"{name} must be non-negative")
        if self.runtime_seconds < 0:
            raise ValueError("runtime_seconds must be non-negative")
        if self.status is CodeExecutionStatus.SUCCEEDED and self.exit_code not in (None, 0):
            raise ValueError("successful execution cannot have a non-zero exit code")
        if self.status in {CodeExecutionStatus.FAILED, CodeExecutionStatus.REJECTED, CodeExecutionStatus.TIMED_OUT}:
            if not (self.failure_reason or "").strip():
                raise ValueError("failed or rejected execution requires failure_reason")
        if self.status is not CodeExecutionStatus.NOT_REQUESTED:
            if not (self.sandbox_ref or "").strip():
                raise ValueError("executed requests require sandbox provenance")


__all__ = [
    "CodeExecutionStatus",
    "CodeExecutionPolicy",
    "CodeExecutionRequest",
    "CodeExecutionResult",
]