"""Deterministic, privacy-safe stage receipts for resumable work."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
import json
from typing import Any


def fingerprint(value: Any) -> str:
    """Return a stable SHA-256 fingerprint for JSON-compatible metadata."""
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return sha256(encoded).hexdigest()


@dataclass(frozen=True)
class StageReceipt:
    request_fingerprint: str
    stage: str
    input_fingerprint: str
    output_fingerprint: str
    method: str
    provider: str = "local"
    parent_receipt_fingerprint: str | None = None
    resource_units: int = 0
    attempt: int = 1
    status: str = "completed"
    resume_eligible: bool = True
    created_at: str | None = None
    expires_at: str | None = None

    def __post_init__(self) -> None:
        for name, value, limit in (
            ("request_fingerprint", self.request_fingerprint, 128),
            ("stage", self.stage, 64),
            ("input_fingerprint", self.input_fingerprint, 128),
            ("output_fingerprint", self.output_fingerprint, 128),
            ("method", self.method, 96),
            ("provider", self.provider, 64),
            ("status", self.status, 32),
        ):
            if not value.strip():
                raise ValueError(f"{name} must not be empty")
            if len(value) > limit:
                raise ValueError(f"{name} exceeds bounded length")
        if self.parent_receipt_fingerprint is not None and not self.parent_receipt_fingerprint.strip():
            raise ValueError("parent_receipt_fingerprint must be non-empty when provided")
        if self.resource_units < 0:
            raise ValueError("resource_units must be non-negative")
        if self.attempt < 1:
            raise ValueError("attempt must be positive")
        for name, value in (("created_at", self.created_at), ("expires_at", self.expires_at)):
            if value is not None:
                if len(value) > 64:
                    raise ValueError(f"{name} exceeds bounded length")
                try:
                    datetime.fromisoformat(value.replace("Z", "+00:00"))
                except ValueError as exc:
                    raise ValueError(f"{name} must be an ISO-8601 timestamp") from exc
        if self.created_at and self.expires_at:
            created = datetime.fromisoformat(self.created_at.replace("Z", "+00:00"))
            expires = datetime.fromisoformat(self.expires_at.replace("Z", "+00:00"))
            if created.tzinfo is None or expires.tzinfo is None:
                raise ValueError("receipt timestamps must include a timezone")
            if expires <= created:
                raise ValueError("expires_at must be later than created_at")

    def fingerprint(self) -> str:
        return fingerprint({
            "request_fingerprint": self.request_fingerprint,
            "stage": self.stage,
            "input_fingerprint": self.input_fingerprint,
            "output_fingerprint": self.output_fingerprint,
            "method": self.method,
            "provider": self.provider,
            "parent_receipt_fingerprint": self.parent_receipt_fingerprint,
            "resource_units": self.resource_units,
            "attempt": self.attempt,
            "status": self.status,
            "resume_eligible": self.resume_eligible,
            "created_at": self.created_at,
            "expires_at": self.expires_at,
        })


def can_resume(
    receipt: StageReceipt,
    *,
    request_fingerprint: str,
    input_fingerprint: str,
    now: datetime | None = None,
) -> bool:
    """Return whether a completed receipt is still eligible for deterministic resume."""
    if not (
        receipt.resume_eligible
        and receipt.status == "completed"
        and receipt.request_fingerprint == request_fingerprint
        and receipt.input_fingerprint == input_fingerprint
    ):
        return False
    if receipt.expires_at is None:
        return True
    current = now or datetime.now(timezone.utc)
    if current.tzinfo is None:
        raise ValueError("now must include a timezone")
    expires = datetime.fromisoformat(receipt.expires_at.replace("Z", "+00:00"))
    return current < expires


def validate_chain(
    receipts: tuple[StageReceipt, ...],
    *,
    max_resource_units: int | None = None,
) -> bool:
    """Validate receipt linkage and optionally bound cumulative resource consumption."""
    if max_resource_units is not None and max_resource_units < 0:
        raise ValueError("max_resource_units must be non-negative")
    if not receipts:
        return True
    request = receipts[0].request_fingerprint
    previous = None
    total_resource_units = 0
    for receipt in receipts:
        if receipt.request_fingerprint != request:
            return False
        if previous is not None and receipt.parent_receipt_fingerprint != previous:
            return False
        total_resource_units += receipt.resource_units
        if max_resource_units is not None and total_resource_units > max_resource_units:
            raise ValueError("receipt chain exceeds max_resource_units")
        previous = receipt.fingerprint()
    return True
