from decimal import Decimal
from datetime import datetime, timezone

from backend.intelligence.contradiction import (
    TypedClaim,
    bounded_typed_candidate_pairs,
    detect_typed_contradiction,
    normalize_quantity,
)


def test_quantity_units_normalize_deterministically():
    assert normalize_quantity("1000", "g").value == Decimal("1.000")
    assert normalize_quantity("39.3700787402", "in").dimension == "length"


def test_equivalent_quantities_are_not_contradictions():
    left = TypedClaim("a", "device", "weight", "1000", "quantity", unit="g")
    right = TypedClaim("b", "device", "weight", "1", "quantity", unit="kg")
    assert detect_typed_contradiction(left, right) is None


def test_tolerance_prevents_false_contradiction():
    left = TypedClaim("a", "device", "weight", "1000", "numeric", unit="g", tolerance=Decimal("2"))
    right = TypedClaim("b", "device", "weight", "1001", "numeric", unit="g")
    assert detect_typed_contradiction(left, right) is None


def test_explicit_negation_is_a_typed_conflict():
    left = TypedClaim("a", "device", "wireless", "enabled", "boolean", negated=True)
    right = TypedClaim("b", "device", "wireless", "enabled", "boolean", negated=False)
    assert detect_typed_contradiction(left, right) is not None


def test_different_versions_are_not_candidates_in_same_bucket():
    a = TypedClaim("a", "device", "status", "old", "text", version="v1")
    b = TypedClaim("b", "device", "status", "new", "text", version="v2")
    pairs = bounded_typed_candidate_pairs([a, b])
    assert pairs == ()


def test_commercial_qualifiers_do_not_create_false_conflict():
    a = TypedClaim("a", "device", "price", "100", "text", qualifier="starts_at")
    b = TypedClaim("b", "device", "price", "120", "text", qualifier="exact")
    assert detect_typed_contradiction(a, b) is None


def test_candidate_order_is_source_invariant():
    now = datetime(2026, 9, 18, tzinfo=timezone.utc)
    a = TypedClaim("a", "device", "price", "100", "numeric", unit="g", valid_from=now)
    b = TypedClaim("b", "device", "price", "200", "numeric", unit="g", valid_from=now)
    assert bounded_typed_candidate_pairs([a, b]) == bounded_typed_candidate_pairs([b, a])
