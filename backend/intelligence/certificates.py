"""Compatibility facade for the canonical evidence certificate contract.

`backend.evidence_certificate.EvidenceCertificate` is the single certificate
implementation. This module preserves the historical intelligence import path
and its source-id-aware constructor behavior without maintaining a second schema.
"""

from backend.evidence_certificate import EvidenceCertificate, create_certificate, verify_certificate

__all__ = ["EvidenceCertificate", "create_certificate", "verify_certificate"]
