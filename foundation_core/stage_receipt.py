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


def _parse_timestamp(value: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("timestamp must be ISO-8601") from exc
    if parsed.tzinfo is None:
        raise ValueError("timestamp must be timezone-aware")
    return parsed


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
        if self.created_at is not None and len(self.created_at) > 64:
            raise ValueError("created_at exceeds bounded length")
        if self.expires_at is not None and len(self.expires_at) > 64:
            raise ValueError("expires_at exceeds bounded length")
        if self.created_at is not None and self.expires_at is not None and _parse_timestamp(self.expires_at) < _parse_timestamp(self.created_at):
            raise ValueError("expires_at must not precede created_at")

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
    if not (receipt.resume_eligible and receipt.status == "completed" and receipt.request_fingerprint == request_fingerprint and receipt.input_fingerprint == input_fingerprint):
        return False
    if receipt.expires_at is None:
        return True
    current = now or datetime.now(timezone.utc)
    if current.tzinfo is None:
        raise ValueError("now must be timezone-aware")
    return current <= _parse_timestamp(receipt.expires_at)


def validate_chain(receipts: tuple[StageReceipt, ...], *, max_resource_units: int | None = None) -> bool:
    """Validate structural receipt linkage and optional cumulative resource budget."""
    if max_resource_units is not None and max_resource_units < 0:
        raise ValueError("max_resource_units must be non-negative")
    if not receipts:
        return True
    request = receipts[0].request_fingerprint
    previous = None
    total = 0
    for receipt in receipts:
        if receipt.request_fingerprint != request:
            return False
        if previous is not None and receipt.parent_receipt_fingerprint != previous:
            return False
        total += receipt.resource_units
        if max_resource_units is not None and total > max_resource_units:
            return False
        previous = receipt.fingerprint()
    return True
