from datetime import datetime, timezone

import pytest

from backend.intelligence.contradiction import (
    TypedClaim,
    bounded_typed_candidate_pairs,
    bucket_typed_claims,
)
from backend.intelligence.transformation_lineage import (
    SpanMappingState,
    content_fingerprint,
    create_transformation_lineage,
)


def claim(cid, entity="E", predicate="P", scope=None, valid_from=None, valid_until=None):
    return TypedClaim(
        cid, entity, predicate, "value", "text",
        scope=scope, valid_from=valid_from, valid_until=valid_until,
        unit="u", qualifier="q",
    )


def test_candidate_bucketing_is_deterministic_and_scope_aware():
    claims = [claim("b"), claim("a"), claim("c", entity="F"), claim("d", scope="US")]
    buckets = bucket_typed_claims(claims)
    assert list(buckets) == sorted(buckets)
    assert [x.claim_id for x in buckets[("e", "p", "*")]] == ["a", "b"]
    assert [x.claim_id for x in buckets[("f", "p", "*")]] == ["c"]


def test_candidate_pairs_are_source_order_invariant_and_bounded():
    claims = [claim(str(i)) for i in range(20)]
    forward = [(a.claim_id, b.claim_id) for a, b in bounded_typed_candidate_pairs(claims, max_pairs=10)]
    reverse = [(a.claim_id, b.claim_id) for a, b in bounded_typed_candidate_pairs(list(reversed(claims)), max_pairs=10)]
    assert forward == reverse
    assert len(forward) == 10
    with pytest.raises(ValueError):
        bounded_typed_candidate_pairs(claims, max_pairs=0)


def test_transformation_fingerprints_and_lossy_mapping_are_explicit():
    assert content_fingerprint("hello") == content_fingerprint(b"hello")
    lineage = create_transformation_lineage(
        "artifact-1",
        "html_normalization",
        "v1",
        "<p>Hello</p>",
        "Hello",
        span_mapping=SpanMappingState.MAPPED,
        execution_identity="exec-1",
        transformed_at=datetime(2026, 9, 18, tzinfo=timezone.utc),
    )
    lineage.validate()
    assert lineage.parent_artifact_id == "artifact-1"
    assert lineage.input_fingerprint != lineage.output_fingerprint


def test_lossy_transformation_requires_warning_and_exact_mapping_requires_same_content():
    with pytest.raises(ValueError, match="lossy"):
        create_transformation_lineage(
            "artifact-1", "ocr", "v1", "a", "b",
            span_mapping=SpanMappingState.LOSSY,
        )
    with pytest.raises(ValueError, match="exact mapping"):
        create_transformation_lineage(
            "artifact-1", "identity", "v1", "a", "b",
            span_mapping=SpanMappingState.EXACT,
        )
