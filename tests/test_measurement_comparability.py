from decimal import Decimal

import pytest

from backend.intelligence.comparability import (
    COMPARABILITY_SCHEMA,
    ComparabilityResult,
    ComparabilityState,
    Measurement,
    MeasurementContext,
    classify_comparability,
    normalize_measurement,
)


def ctx(**kwargs):
    return MeasurementContext(entity="cpu", provenance_id="src", **kwargs)


def test_measurement_context_validation_matrix():
    ctx().validate()
    ctx(uncertainty_low=Decimal("1"), uncertainty_high=Decimal("2")).validate()
    with pytest.raises(ValueError, match="entity"):
        MeasurementContext(entity=" ", provenance_id="src").validate()
    with pytest.raises(ValueError, match="provenance"):
        MeasurementContext(entity="cpu", provenance_id=" ").validate()
    with pytest.raises(ValueError, match="sample_size"):
        ctx(sample_size=0).validate()
    with pytest.raises(ValueError, match="replication_count"):
        ctx(replication_count=0).validate()
    with pytest.raises(ValueError, match="uncertainty_high"):
        ctx(uncertainty_low=Decimal("5"), uncertainty_high=Decimal("2")).validate()


def test_normalization_handles_missing_unknown_and_known_units():
    assert normalize_measurement(Decimal("1"), None) is None
    assert normalize_measurement(Decimal("1"), "") is None
    assert normalize_measurement(Decimal("1"), "unknown") is None
    normalized = normalize_measurement(Decimal("2"), " kg ")
    assert normalized.value == Decimal("2000")
    assert normalized.dimension == "mass"
    assert normalized.unit == "kg"


def test_result_schema_validation_both_paths():
    result = ComparabilityResult(ComparabilityState.COMPARABLE, ())
    result.validate()
    with pytest.raises(ValueError, match="schema"):
        ComparabilityResult(ComparabilityState.COMPARABLE, (), schema_version="v0").validate()


def test_comparability_entity_mismatch_is_uncomparable():
    left = Measurement(Decimal("1"), ctx(unit="s"))
    right = Measurement(Decimal("1"), MeasurementContext(entity="gpu", provenance_id="src", unit="s"))
    result = classify_comparability(left, right)
    assert result.state is ComparabilityState.UNCOMPARABLE


@pytest.mark.parametrize("field", [
    "variant", "region", "environment", "software_revision",
    "methodology", "tool_version", "workload", "population",
])
def test_different_context_fields_are_uncomparable(field):
    left = Measurement(Decimal("1"), ctx(unit="s", **{field: "a"}))
    right = Measurement(Decimal("1"), ctx(unit="s", **{field: "b"}))
    result = classify_comparability(left, right)
    assert result.state is ComparabilityState.UNCOMPARABLE
    assert any(reason.startswith("different:") for reason in result.reasons)


def test_missing_context_is_partial():
    left = Measurement(Decimal("1"), ctx(unit="s", methodology="tool"))
    right = Measurement(Decimal("1"), ctx(unit="s"))
    result = classify_comparability(left, right)
    assert result.state is ComparabilityState.PARTIAL
    assert "missing:methodology" in result.reasons


def test_unknown_unit_is_unknown():
    left = Measurement(Decimal("1"), ctx(unit="score-a"))
    right = Measurement(Decimal("1"), ctx(unit="score-b"))
    assert classify_comparability(left, right).state is ComparabilityState.UNKNOWN


def test_dimension_mismatch_is_uncomparable():
    left = Measurement(Decimal("1"), ctx(unit="bytes"))
    right = Measurement(Decimal("1"), ctx(unit="s"))
    result = classify_comparability(left, right)
    assert result.state is ComparabilityState.UNCOMPARABLE


def test_identical_conditions_are_comparable_with_delta():
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


def test_measurement_validate_delegates_context():
    measurement = Measurement(Decimal("1"), ctx(unit="s"))
    measurement.validate()
