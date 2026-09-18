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
