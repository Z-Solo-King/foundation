"""Compatibility facade for the canonical evidence certificate contract.

`backend.evidence_certificate.EvidenceCertificate` is the single certificate
implementation. This module preserves the historical intelligence import path
and its source-id-aware constructor behavior without maintaining a second schema.
"""

from backend.evidence_certificate import EvidenceCertificate, create_certificate
from backend.evidence_certificate import verify_certificate as _verify_certificate


def verify_certificate(observation, certificate) -> bool:
    """Preserve historical intelligence behavior for invalid spans."""
    try:
        return _verify_certificate(observation, certificate)
    except ValueError:
        return False


__all__ = ["EvidenceCertificate", "create_certificate", "verify_certificate"]
