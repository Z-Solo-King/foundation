from dataclasses import replace
from datetime import datetime, timezone

import pytest

from backend.intelligence.snapshots import ClaimSnapshot, DocumentVersion, changed


def test_document_version_fingerprint_and_validation():
    version = DocumentVersion(
        "v2", "doc-1", "0" * 64, datetime(2026, 9, 13, tzinfo=timezone.utc),
        parent_version_id="v1", extractor_version="extractor-v2", mapper_version="mapper-v1", retention_state="retained",
    )
    version.validate()
    assert len(version.fingerprint()) == 64
    with pytest.raises(ValueError): replace(version, version_id="").validate()
    with pytest.raises(ValueError): replace(version, content_hash="short").validate()
    with pytest.raises(ValueError): replace(version, mapper_version="x" * 4097).validate()


def test_claim_snapshot_version_metadata_and_change_detection():
    first = ClaimSnapshot.create("s1", "c1", "one", document_version_id="v1", evidence_fingerprint="e1", revision_number=1)
    second = ClaimSnapshot.create("s2", "c1", "two", document_version_id="v2", evidence_fingerprint="e2", revision_number=2, parent_snapshot_id="s1")
    assert first.revision_number == 1
    assert second.parent_snapshot_id == "s1"
    assert changed(first, second)
    with pytest.raises(ValueError): replace(first, revision_number=0).validate()
    with pytest.raises(ValueError): replace(first, claim_id="").validate()
    with pytest.raises(ValueError): replace(first, evidence_fingerprint="x" * 4097).validate()
