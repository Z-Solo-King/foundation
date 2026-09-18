from datetime import datetime, timezone

import pytest

from backend.intelligence.transformation_lineage import (
    SpanMappingState,
    TransformationLineage,
    content_fingerprint,
    create_transformation_lineage,
)


def test_content_fingerprint_is_stable_and_type_consistent():
    assert content_fingerprint("hello") == content_fingerprint(b"hello")
    assert len(content_fingerprint("hello")) == 64


def test_exact_transformation_requires_identical_content_fingerprint():
    lineage = create_transformation_lineage(
        "artifact-1",
        "normalize",
        "v1",
        "same",
        "same",
        span_mapping=SpanMappingState.EXACT,
        execution_identity="exec-1",
        language_from="en",
        language_to="en",
        transformed_at=datetime(2026, 9, 18, tzinfo=timezone.utc),
    )
    lineage.validate()
    assert lineage.input_fingerprint == lineage.output_fingerprint
    assert lineage.span_mapping is SpanMappingState.EXACT


def test_mapped_transformation_preserves_parent_and_language_provenance():
    lineage = create_transformation_lineage(
        "artifact-1",
        "translate",
        "v2",
        "source language",
        "translated text",
        span_mapping=SpanMappingState.MAPPED,
        execution_identity="exec-1",
        language_from="fr",
        language_to="en",
        transformed_at=datetime(2026, 9, 18, tzinfo=timezone.utc),
    )
    assert lineage.parent_artifact_id == "artifact-1"
    assert lineage.language_from == "fr"
    assert lineage.language_to == "en"
    assert lineage.execution_identity == "exec-1"
    lineage.validate()


def test_lossy_transformation_requires_explicit_warning():
    with pytest.raises(ValueError, match="lossy"):
        create_transformation_lineage(
            "artifact-1",
            "summarize",
            "v1",
            "source",
            "summary",
            span_mapping=SpanMappingState.LOSSY,
            transformed_at=datetime(2026, 9, 18, tzinfo=timezone.utc),
        )


def test_invalid_timezone_or_fingerprint_fails_closed():
    with pytest.raises(ValueError, match="timezone-aware"):
        TransformationLineage(
            "artifact-1",
            "translate",
            "v1",
            "a" * 64,
            "b" * 64,
            SpanMappingState.MAPPED,
            datetime(2026, 9, 18),
        ).validate()

    with pytest.raises(ValueError, match="SHA-256"):
        TransformationLineage(
            "artifact-1",
            "translate",
            "v1",
            "not-a-fingerprint",
            "b" * 64,
            SpanMappingState.MAPPED,
            datetime(2026, 9, 18, tzinfo=timezone.utc),
        ).validate()


def test_create_lineage_supports_unmapped_outputs_without_claiming_exactness():
    lineage = create_transformation_lineage(
        "artifact-1",
        "extract",
        "v1",
        b"input",
        b"output",
        span_mapping=SpanMappingState.UNMAPPED,
        warning="span offsets unavailable after conversion",
        transformed_at=datetime(2026, 9, 18, tzinfo=timezone.utc),
    )
    lineage.validate()
    assert lineage.span_mapping is SpanMappingState.UNMAPPED
