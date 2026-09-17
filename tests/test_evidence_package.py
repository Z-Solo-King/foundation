import hashlib
import hmac

import pytest

from backend.evidence_package import EvidencePackage, parse_trusted_package


def package(key=b"test-key"):
    base = EvidencePackage("evidence-package/v1", "pkg-1", "run-1", ("v1",), ("span-1",), ({"claim": "x"},), "synthesis", "0" * 64, "operations", "")
    digest = hashlib.sha256(base.canonical_bytes()).hexdigest()
    unsigned = EvidencePackage(base.schema, base.package_id, base.research_run_id, base.source_versions, base.evidence_spans, base.claims, base.synthesis, digest, base.signer, "")
    signature = hmac.new(key, unsigned.canonical_bytes(), hashlib.sha256).hexdigest()
    signed = EvidencePackage(unsigned.schema, unsigned.package_id, unsigned.research_run_id, unsigned.source_versions, unsigned.evidence_spans, unsigned.claims, unsigned.synthesis, unsigned.artifact_digest, unsigned.signer, signature)
    return unsigned, signed


def test_trusted_package_requires_valid_digest_and_signature():
    _, signed = package()
    assert parse_trusted_package(signed.__dict__, b"test-key").package_id == "pkg-1"


def test_invalid_signature_is_rejected():
    _, signed = package()
    bad = {**signed.__dict__, "signature": "0" * 64}
    with pytest.raises(ValueError, match="signature"):
        parse_trusted_package(bad, b"test-key")


def test_missing_lineage_is_rejected():
    _, signed = package()
    bad = {**signed.__dict__, "source_versions": ()}
    with pytest.raises(ValueError, match="lineage"):
        parse_trusted_package(bad, b"test-key")
