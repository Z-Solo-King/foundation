from datetime import datetime, timezone
from hashlib import sha256

import pytest

from backend.intelligence.observations import EvidenceSpan, Observation


def test_enriched_observation_preserves_legacy_construction_and_fingerprints():
    content = "Primary source says the launch is on September 13, 2026."
    observed = datetime(2026, 9, 13, tzinfo=timezone.utc)
    observation = Observation(
        "obs-1",
        source_id="source-1",
        source_family_id="family-1",
        document_version_id="doc-v1",
        source_url="https://example.com/source",
        content=content,
        observed_at=observed,
        retrieved_at=observed,
        published_at=observed,
        author="Example Publisher",
        language="en",
        title="Launch date",
        extraction_method="html",
        acquisition_method="static_html",
        raw_artifact_ref="artifact-1",
        content_sha256=sha256(content.encode()).hexdigest(),
        quality=0.9,
        provenance={"publisher": "example"},
        policy_state="allowed",
        extractor_version="extractor-1",
    )
    legacy = Observation("obs-2", "https://example.com/source", content, observed)
    assert observation.source_family_id == "family-1"
    assert legacy.source_id is None
    assert observation.fingerprint() != legacy.fingerprint()
    assert EvidenceSpan("obs-1", 0, 11).text_from(observation) == "Primary sou"


def test_observation_rejects_invalid_hash_and_quality():
    content = "hello"
    digest = sha256(content.encode()).hexdigest()
    with pytest.raises(ValueError):
        Observation("obs", "https://example.com", content, content_sha256="bad")
    with pytest.raises(ValueError):
        Observation("obs", "https://example.com", content, quality=1.1)
    good = Observation("obs", "https://example.com", content, content_sha256=digest)
    assert good.content_sha256 == digest
