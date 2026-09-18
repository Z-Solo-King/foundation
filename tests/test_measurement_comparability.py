from decimal import Decimal

import pytest

from backend.intelligence.comparability import (
    ComparabilityState,
    Measurement,
    MeasurementContext,
    classify_comparability,
    normalize_measurement,
)


def ctx(**kwargs):
    return MeasurementContext(entity="cpu", provenance_id="src", **kwargs)


def test_identical_conditions_are_comparable():
    common = dict(
        unit="ms",
        variant="v1",
        region="global",
        environment="linux",
        software_revision="sw-1",
        methodology="tool-v1",
        tool_version="tool-1",
        workload="steady",
        population="n=10",
    )
    left = Measurement(Decimal("1000"), ctx(**common))
    right = Measurement(Decimal("1"), ctx(**{**common, "unit": "s"}))
    result = classify_comparability(left, right)
    assert result.state is ComparabilityState.COMPARABLE
    assert result.normalized_delta == 0


def test_unit_conversion_is_deterministic_and_preserves_metadata():
    normalized = normalize_measurement(Decimal("2"), "kg")
    assert normalized is not None
    assert normalized.value == Decimal("2000")
    assert normalized.dimension == "mass"


def test_variant_change_is_uncomparable():
    left = Measurement(Decimal("1"), ctx(unit="s", variant="v1"))
    right = Measurement(Decimal("1"), ctx(unit="s", variant="v2"))
    assert classify_comparability(left, right).state is ComparabilityState.UNCOMPARABLE


def test_missing_test_context_is_partial_not_fabricated():
    left = Measurement(Decimal("1"), ctx(unit="s", methodology="tool-v1"))
    right = Measurement(Decimal("1"), ctx(unit="s"))
    result = classify_comparability(left, right)
    assert result.state is ComparabilityState.PARTIAL
    assert "missing:methodology" in result.reasons


def test_unknown_units_are_not_normalized_as_comparable():
    left = Measurement(Decimal("1"), ctx(unit="score-a"))
    right = Measurement(Decimal("1"), ctx(unit="score-b"))
    assert classify_comparability(left, right).state is ComparabilityState.UNKNOWN


def test_uncertainty_ranges_are_validated():
    with pytest.raises(ValueError, match="uncertainty_high"):
        MeasurementContext(
            entity="cpu",
            provenance_id="src",
            uncertainty_low=Decimal("5"),
            uncertainty_high=Decimal("2"),
        ).validate()
