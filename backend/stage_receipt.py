"""Compatibility exports for the canonical public stage-receipt primitive."""

from foundation_core.stage_receipt import StageReceipt, can_resume, fingerprint, validate_chain

__all__ = ["StageReceipt", "can_resume", "fingerprint", "validate_chain"]
