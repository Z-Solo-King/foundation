from backend.intelligence.contradiction import TypedClaim, detect_contradiction, detect_typed_contradiction


def c(cid, value, value_type="numeric", **kwargs):
    return TypedClaim(cid, "product-1", "price", value, value_type, **kwargs)


def test_numeric_difference_is_contradiction():
    result = detect_typed_contradiction(c("a", 10, unit="USD"), c("b", 12, unit="USD"))
    assert result is not None
    assert "numeric" in result.reason


def test_different_units_are_not_compared():
    assert detect_typed_contradiction(c("a", 10, unit="USD"), c("b", 12, unit="EUR")) is None


def test_boolean_values_conflict():
    result = detect_typed_contradiction(c("a", True, "boolean"), c("b", False, "boolean"))
    assert result is not None


def test_different_versions_do_not_conflict():
    assert detect_typed_contradiction(c("a", 10, unit="USD", version="v1"), c("b", 12, unit="USD", version="v2")) is None


def test_legacy_negation_detection_remains_available():
    assert detect_contradiction("available", "unavailable") is not None
