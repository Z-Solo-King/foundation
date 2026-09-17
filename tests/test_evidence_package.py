import hashlib
import hmac

import pytest

from backend.evidence_package import EvidencePackage, parse_trusted_package


def package(key=b"test-key"):
    base = EvidencePackage(
        "evidence-package/v1", "pkg-1", "run-1", ("v1",), ("span-1",), ({"claim": "x"},),
        "synthesis", "0" * 64, "operations", ""
    )
    digest = hashlib.sha256(base.canonical_bytes()).hexdigest()
    unsigned = EvidencePackage(
        base.schema, base.package_id, base.research_run_id, base.source_versions,
        base.evidence_spans, base.claims, base.synthesis, digest, base.signer, ""
    )
    signature = hmac.new(key, unsigned.canonical_bytes(), hashlib.sha256).hexdigest()
    return EvidencePackage(
        unsigned.schema, unsigned.package_id, unsigned.research_run_id, unsigned.source_versions,
        unsigned.evidence_spans, unsigned.claims, unsigned.synthesis, unsigned.artifact_digest,
        unsigned.signer, signature
    )


def test_trusted_package_requires_valid_digest_and_signature():
    signed = package()
    parsed = parse_trusted_package(signed.__dict__, b"test-key")
    assert parsed.package_id == "pkg-1"
    assert parsed.payload()["artifact_digest"] == signed.artifact_digest


def test_invalid_signature_is_rejected():
    signed = package()
    with pytest.raises(ValueError, match="signature"):
        parse_trusted_package({**signed.__dict__, "signature": "0" * 64}, b"test-key")


def test_missing_lineage_is_rejected():
    signed = package()
    with pytest.raises(ValueError, match="lineage"):
        parse_trusted_package({**signed.__dict__, "source_versions": ()}, b"test-key")


def test_digest_tampering_is_rejected():
    signed = package()
    with pytest.raises(ValueError, match="digest"):
        parse_trusted_package({**signed.__dict__, "synthesis": "tampered"}, b"test-key")


def test_malformed_digest_is_rejected():
    signed = package()
    with pytest.raises(ValueError, match="SHA-256"):
        parse_trusted_package({**signed.__dict__, "artifact_digest": "not-a-digest"}, b"test-key")


def test_missing_trust_key_is_rejected():
    signed = package()
    with pytest.raises(ValueError, match="trust key"):
        parse_trusted_package(signed.__dict__, b"")


def test_non_object_package_is_rejected():
    with pytest.raises(ValueError, match="must be an object"):
        parse_trusted_package([], b"test-key")


def test_invalid_schema_identity_and_synthesis_are_rejected():
    signed = package()
    for field, value, message in (
        ("schema", "bad", "unsupported"),
        ("package_id", "", "identity"),
        ("synthesis", "", "synthesis"),
    ):
        with pytest.raises(ValueError, match=message):
            parse_trusted_package({**signed.__dict__, field: value}, b"test-key")
