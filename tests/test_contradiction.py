from datetime import datetime
from decimal import Decimal
from backend.intelligence.contradiction import TypedClaim, detect_contradiction, detect_typed_contradiction, bounded_typed_candidate_pairs


def c(cid, value, value_type="numeric", **kwargs):
    return TypedClaim(cid, "product-1", "price", value, value_type, **kwargs)


def test_numeric_difference_is_contradiction_and_tolerance_is_respected():
    assert detect_typed_contradiction(c("a", 10, unit="kg"), c("b", 9000, unit="g")) is not None
    assert detect_typed_contradiction(c("a", 10, unit="kg", tolerance=Decimal("1")), c("b", 10.5, unit="kg")) is None


def test_unknown_or_incompatible_units_are_not_compared():
    assert detect_typed_contradiction(c("a", 10, unit="USD"), c("b", 12, unit="EUR")) is None
    assert detect_typed_contradiction(c("a", 10, unit="kg"), c("b", 12, unit="s")) is None


def test_boolean_values_conflict():
    result = detect_typed_contradiction(c("a", True, "boolean"), c("b", False, "boolean"))
    assert result is not None


def test_different_versions_do_not_conflict():
    assert detect_typed_contradiction(c("a", 10, unit="USD", version="v1"), c("b", 12, unit="USD", version="v2")) is None


def test_dates_and_temporal_validity_are_typed():
    assert detect_typed_contradiction(
        c("a", "2026-09-18", "date"),
        c("b", "2026-09-19", "date"),
    ) is not None
    assert detect_typed_contradiction(
        c("a", "2026-09-18", "date", valid_until=datetime(2026, 9, 18)),
        c("b", "2026-09-19", "date", valid_from=datetime(2026, 9, 19, 1)),
    ) is None


def test_qualifiers_and_explicit_negation_are_distinct():
    assert detect_typed_contradiction(
        c("a", "100", "text", unit="USD", qualifier="starts_at"),
        c("b", "120", "text", unit="USD", qualifier="exact"),
    ) is not None
    assert detect_typed_contradiction(
        c("a", "available", "text", unit="text", negated=True),
        c("b", "available", "text", unit="text", negated=False),
    ) is not None


def test_different_scopes_and_unknown_values_do_not_conflict():
    assert detect_typed_contradiction(
        c("a", 10, scope="US", unit="kg"),
        c("b", 12, scope="EU", unit="kg"),
    ) is None
    assert detect_typed_contradiction(c("a", "x", "text", unit="x"), c("b", "x", "text", unit="x")) is None


def test_candidate_bucket_is_bounded_and_order_invariant():
    claims=[c(str(i), i, unit="kg") for i in range(30)]
    forward=bounded_typed_candidate_pairs(claims, max_pairs=10)
    reverse=bounded_typed_candidate_pairs(list(reversed(claims)), max_pairs=10)
    assert [(a.claim_id,b.claim_id) for a,b in forward]==[(a.claim_id,b.claim_id) for a,b in reverse]


def test_legacy_negation_detection_remains_available():
    assert detect_contradiction("available", "unavailable") is not None


def test_numeric_pair_rejects_invalid_raw_fallback_without_false_contradiction():
    assert detect_typed_contradiction(
        c("a", "not-a-number", unit="u"),
        c("b", 2, unit="u"),
    ) is None


def test_quantity_unit_mismatch_and_tolerance_branches_are_bounded():
    assert detect_typed_contradiction(
        c("a", 1, "quantity", unit="kg"),
        c("b", 1, "quantity", unit="s"),
    ) is None
    assert detect_typed_contradiction(
        c("a", 1, "quantity", unit="kg", tolerance=2),
        c("b", 999, "quantity", unit="g"),
    ) is None
