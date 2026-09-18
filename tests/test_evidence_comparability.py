from datetime import datetime, timezone

import pytest

from backend.intelligence.comparability import (
    ComparabilityState,
    ComparabilityResult,
    MeasurementContext,
    MeasurementObservation,
    UnitConversion,
    compare_measurements,
)


UTC = timezone.utc
BASE = datetime(2026, 9, 18, 10, 0, tzinfo=UTC)


def ctx(**changes):
    values = dict(
        entity="device-x",
        variant="base",
        region="US",
        environment="linux",
        software_revision="v1",
        methodology="bench-v1",
        tool_version="tool-v1",
    )
    values.update(changes)
    return MeasurementContext(**values)


def obs(**changes):
    values = dict(
        measurement_id="m1",
        context=ctx(),
        value=100,
        unit="ms",
        observed_at=BASE,
        sample_size=10,
        population="users",
        uncertainty_low=98,
        uncertainty_high=102,
        replication_count=2,
        provenance_ids=("obs-1",),
    )
    values.update(changes)
    return MeasurementObservation(**values)


def test_identical_contexts_are_comparable_and_fingerprinted():
    result = compare_measurements(obs(), obs(measurement_id="m2", value=101))
    assert result.state is ComparabilityState.COMPARABLE
    assert result.normalized_unit == "ms"
    assert result.value_difference == 1
    assert result.context_fingerprint == compare_measurements(obs(), obs(measurement_id="m2", value=101)).context_fingerprint


@pytest.mark.parametrize(
    "changes, reason",
    [
        ({"variant": "other"}, "variant_mismatch"),
        ({"region": "EU"}, "region_mismatch"),
        ({"environment": "windows"}, "environment_mismatch"),
        ({"software_revision": "v2"}, "software_revision_mismatch"),
        ({"methodology": "bench-v2"}, "methodology_mismatch"),
        ({"tool_version": "tool-v2"}, "tool_version_mismatch"),
    ],
)
def test_context_mismatch_is_uncomparable(changes, reason):
    result = compare_measurements(obs(), obs(context=ctx(**changes)))
    assert result.state is ComparabilityState.UNCOMPARABLE
    assert reason in result.reason_codes


def test_entity_mismatch_is_uncomparable():
    result = compare_measurements(obs(), obs(context=ctx(entity="device-y")))
    assert result.state is ComparabilityState.UNCOMPARABLE
    assert "entity_mismatch" in result.reason_codes


def test_missing_context_is_unknown_without_equivalence_rule():
    result = compare_measurements(obs(context=ctx(region=None)), obs(measurement_id="m2"))
    assert result.state is ComparabilityState.UNKNOWN
    assert "region_missing" in result.reason_codes


def test_observation_time_window_and_unit_conversion():
    conversion = UnitConversion("s", "ms", 1000.0)
    left = obs(value=1, unit="s")
    right = obs(measurement_id="m2", value=1000, unit="ms")
    result = compare_measurements(left, right, conversion=conversion, max_age_seconds=5)
    assert result.state is ComparabilityState.COMPARABLE
    assert result.normalized_left == 1000
    assert result.normalized_right == 1000


def test_time_mismatch_without_window_is_unknown():
    result = compare_measurements(
        obs(),
        obs(measurement_id="m2", observed_at=BASE.replace(hour=11)),
    )
    assert result.state is ComparabilityState.UNKNOWN
    assert "observation_time_unspecified" in result.reason_codes


def test_time_mismatch_outside_window_is_uncomparable():
    result = compare_measurements(
        obs(),
        obs(measurement_id="m2", observed_at=BASE.replace(hour=11)),
        max_age_seconds=5,
    )
    assert result.state is ComparabilityState.UNCOMPARABLE


def test_validation_and_conversion_errors():
    with pytest.raises(ValueError, match="scale"):
        UnitConversion("s", "ms", 0).validate()
    with pytest.raises(ValueError, match="positive"):
        obs(sample_size=0).validate()
    with pytest.raises(ValueError, match="uncertainty range"):
        obs(uncertainty_low=5, uncertainty_high=1).validate()
    with pytest.raises(ValueError, match="provenance"):
        obs(provenance_ids=("",)).validate()
    with pytest.raises(ValueError, match="entity"):
        ctx(entity="").validate()


def test_comparability_result_validation():
    with pytest.raises(ValueError, match="tolerance"):
        ComparabilityResult(ComparabilityState.UNKNOWN, (), None, None, None, None, -1, "x").validate()
    with pytest.raises(ValueError, match="normalized"):
        ComparabilityResult(ComparabilityState.COMPARABLE, (), None, None, "ms", 0, 0, "x").validate()
    with pytest.raises(ValueError, match="fingerprint"):
        ComparabilityResult(ComparabilityState.UNKNOWN, (), None, None, None, None, 0, "").validate()


def test_result_serialization():
    result = compare_measurements(obs(), obs(measurement_id="m2"))
    payload = result.to_dict()
    assert payload["schema"] == "evidence-comparability/v1"


def test_missing_units_and_incompatible_conversion_are_unknown():
    missing = compare_measurements(
        obs(value=1, unit="s"),
        obs(measurement_id="m2", value=1, unit="ms"),
    )
    assert missing.state is ComparabilityState.UNKNOWN
    assert "unit_conversion_missing" in missing.reason_codes

    incompatible = compare_measurements(
        obs(value=1, unit="s"),
        obs(measurement_id="m2", value=1, unit="kg"),
        conversion=UnitConversion("s", "ms", 1000.0),
    )
    assert incompatible.state is ComparabilityState.UNKNOWN
    assert "unit_conversion_incompatible" in incompatible.reason_codes


def test_reverse_unit_conversion_is_supported():
    conversion = UnitConversion("ms", "s", 0.001)
    result = compare_measurements(
        obs(value=1000, unit="ms"),
        obs(measurement_id="m2", value=1, unit="s"),
        conversion=conversion,
    )
    assert result.state is ComparabilityState.COMPARABLE
    assert result.normalized_left == 1


def test_unknown_time_context_prevents_comparable_state():
    result = compare_measurements(
        obs(context=ctx(region=None)),
        obs(measurement_id="m2"),
    )
    assert result.state is ComparabilityState.UNKNOWN


def test_invalid_compare_limits_are_rejected():
    with pytest.raises(ValueError, match="tolerance"):
        compare_measurements(obs(), obs(measurement_id="m2"), tolerance=-1)
    with pytest.raises(ValueError, match="max_age_seconds"):
        compare_measurements(obs(), obs(measurement_id="m2"), max_age_seconds=-1)


def test_unit_conversion_and_observation_validation_edges():
    with pytest.raises(ValueError, match="source_unit"):
        UnitConversion("", "ms", 1).validate()
    with pytest.raises(ValueError, match="target_unit"):
        UnitConversion("s", "", 1).validate()
    with pytest.raises(ValueError, match="revision"):
        UnitConversion("s", "ms", 1, revision="").validate()
    with pytest.raises(ValueError, match="numeric"):
        UnitConversion("s", "ms", 1).convert("bad")

    with pytest.raises(ValueError, match="measurement value"):
        obs(value=True).validate()
    with pytest.raises(ValueError, match="unit"):
        obs(unit="").validate()
    with pytest.raises(ValueError, match="measurement_id"):
        obs(measurement_id="").validate()
    with pytest.raises(ValueError, match="timezone"):
        obs(observed_at=datetime(2026, 9, 18)).validate()
    with pytest.raises(ValueError, match="population"):
        obs(population="").validate()
    with pytest.raises(ValueError, match="replication"):
        obs(replication_count=-1).validate()


def test_context_optional_fields_must_be_text():
    with pytest.raises(ValueError, match="variant"):
        ctx(variant=1).validate()
    with pytest.raises(ValueError, match="region"):
        ctx(region=1).validate()
    with pytest.raises(ValueError, match="environment"):
        ctx(environment=1).validate()
    with pytest.raises(ValueError, match="software_revision"):
        ctx(software_revision=1).validate()
    with pytest.raises(ValueError, match="methodology"):
        ctx(methodology=1).validate()
    with pytest.raises(ValueError, match="tool_version"):
        ctx(tool_version=1).validate()


def test_normalized_value_and_result_serialization():
    item = obs(value=2, unit="s")
    assert item.normalized_value(None) == (2.0, "s")
    assert item.normalized_value(UnitConversion("s", "ms", 1000.0)) == (2000.0, "ms")
    with pytest.raises(ValueError, match="source"):
        item.normalized_value(UnitConversion("kg", "ms", 1))

    result = compare_measurements(obs(), obs(measurement_id="m2"))
    payload = result.to_dict()
    assert payload["schema"] == "evidence-comparability/v1"


def test_measurement_optional_uncertainty_fields_and_provenance_are_valid():
    obs(uncertainty_low=None, uncertainty_high=10).validate()
    obs(uncertainty_low=10, uncertainty_high=None).validate()
    obs(population=None).validate()
