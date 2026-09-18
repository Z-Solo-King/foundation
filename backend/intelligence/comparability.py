"""Deterministic measurement comparability contract.

Comparability is evidence metadata only. It does not establish truth or replace the
existing verification/publication authorities.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import StrEnum
from hashlib import sha256
import json


SCHEMA = "evidence-comparability/v1"


class ComparabilityState(StrEnum):
    COMPARABLE = "comparable"
    UNCOMPARABLE = "uncomparable"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class UnitConversion:
    source_unit: str
    target_unit: str
    scale: float
    offset: float = 0.0
    revision: str = "v1"

    def validate(self) -> None:
        for name, value in (
            ("source_unit", self.source_unit),
            ("target_unit", self.target_unit),
            ("revision", self.revision),
        ):
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} is required")
        if self.scale <= 0:
            raise ValueError("unit conversion scale must be positive")

    def convert(self, value: float) -> float:
        self.validate()
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            raise ValueError("measurement value must be numeric")
        return float(value) * self.scale + self.offset


@dataclass(frozen=True)
class MeasurementContext:
    entity: str
    variant: str | None
    region: str | None
    environment: str | None
    software_revision: str | None
    methodology: str | None
    tool_version: str | None

    def validate(self) -> None:
        if not self.entity.strip():
            raise ValueError("measurement entity is required")
        for name, value in (
            ("variant", self.variant),
            ("region", self.region),
            ("environment", self.environment),
            ("software_revision", self.software_revision),
            ("methodology", self.methodology),
            ("tool_version", self.tool_version),
        ):
            if value is not None and not isinstance(value, str):
                raise ValueError(f"{name} must be text when supplied")


@dataclass(frozen=True)
class MeasurementObservation:
    measurement_id: str
    context: MeasurementContext
    value: float
    unit: str
    observed_at: datetime
    sample_size: int | None = None
    population: str | None = None
    uncertainty_low: float | None = None
    uncertainty_high: float | None = None
    replication_count: int = 0
    provenance_ids: tuple[str, ...] = ()

    def validate(self) -> None:
        if not self.measurement_id.strip():
            raise ValueError("measurement_id is required")
        self.context.validate()
        if not isinstance(self.value, (int, float)) or isinstance(self.value, bool):
            raise ValueError("measurement value must be numeric")
        if not self.unit.strip():
            raise ValueError("measurement unit is required")
        if self.observed_at.tzinfo is None or self.observed_at.utcoffset() is None:
            raise ValueError("observed_at must be timezone-aware")
        if self.sample_size is not None and self.sample_size < 1:
            raise ValueError("sample_size must be positive when supplied")
        if self.population is not None and not self.population.strip():
            raise ValueError("population must be non-empty when supplied")
        if self.uncertainty_low is not None and self.uncertainty_high is not None:
            if self.uncertainty_low > self.uncertainty_high:
                raise ValueError("uncertainty range is reversed")
        if self.replication_count < 0:
            raise ValueError("replication_count must be non-negative")
        if any(not value.strip() for value in self.provenance_ids):
            raise ValueError("provenance IDs must be non-empty")

    def normalized_value(self, conversion: UnitConversion | None) -> tuple[float, str]:
        self.validate()
        if conversion is None:
            return float(self.value), self.unit
        if conversion.source_unit != self.unit:
            raise ValueError("unit conversion source does not match measurement unit")
        return conversion.convert(float(self.value)), conversion.target_unit


@dataclass(frozen=True)
class ComparabilityResult:
    state: ComparabilityState
    reason_codes: tuple[str, ...]
    normalized_left: float | None
    normalized_right: float | None
    normalized_unit: str | None
    value_difference: float | None
    tolerance: float
    context_fingerprint: str

    def validate(self) -> None:
        if self.tolerance < 0:
            raise ValueError("tolerance must be non-negative")
        if self.state is ComparabilityState.COMPARABLE:
            if self.normalized_left is None or self.normalized_right is None or not self.normalized_unit:
                raise ValueError("comparable measurements require normalized values")
        if not self.context_fingerprint.strip():
            raise ValueError("context_fingerprint is required")

    def to_dict(self) -> dict[str, object]:
        self.validate()
        return {
            "schema": SCHEMA,
            "state": self.state.value,
            "reason_codes": list(self.reason_codes),
            "normalized_left": self.normalized_left,
            "normalized_right": self.normalized_right,
            "normalized_unit": self.normalized_unit,
            "value_difference": self.value_difference,
            "tolerance": self.tolerance,
            "context_fingerprint": self.context_fingerprint,
        }


def _norm(value: str | None) -> str | None:
    if value is None:
        return None
    return " ".join(value.casefold().split()) or None


def _context_fingerprint(left: MeasurementObservation, right: MeasurementObservation) -> str:
    payload = {
        "schema": SCHEMA,
        "left": {
            "entity": _norm(left.context.entity),
            "variant": _norm(left.context.variant),
            "region": _norm(left.context.region),
            "environment": _norm(left.context.environment),
            "software_revision": _norm(left.context.software_revision),
            "methodology": _norm(left.context.methodology),
            "tool_version": _norm(left.context.tool_version),
        },
        "right": {
            "entity": _norm(right.context.entity),
            "variant": _norm(right.context.variant),
            "region": _norm(right.context.region),
            "environment": _norm(right.context.environment),
            "software_revision": _norm(right.context.software_revision),
            "methodology": _norm(right.context.methodology),
            "tool_version": _norm(right.context.tool_version),
        },
    }
    return sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def compare_measurements(
    left: MeasurementObservation,
    right: MeasurementObservation,
    *,
    tolerance: float = 0.0,
    conversion: UnitConversion | None = None,
    max_age_seconds: int | None = None,
) -> ComparabilityResult:
    left.validate()
    right.validate()
    if tolerance < 0:
        raise ValueError("tolerance must be non-negative")
    if max_age_seconds is not None and max_age_seconds < 0:
        raise ValueError("max_age_seconds must be non-negative")

    reasons: list[str] = []
    context_pairs = (
        ("entity", left.context.entity, right.context.entity, True),
        ("variant", _norm(left.context.variant), _norm(right.context.variant), True),
        ("region", _norm(left.context.region), _norm(right.context.region), True),
        ("environment", _norm(left.context.environment), _norm(right.context.environment), True),
        ("software_revision", _norm(left.context.software_revision), _norm(right.context.software_revision), True),
        ("methodology", _norm(left.context.methodology), _norm(right.context.methodology), True),
        ("tool_version", _norm(left.context.tool_version), _norm(right.context.tool_version), True),
    )

    unknown = False
    for name, left_value, right_value, required in context_pairs:
        left_norm = _norm(left_value)
        right_norm = _norm(right_value)
        if left_norm is None or right_norm is None:
            if required and left_norm != right_norm:
                unknown = True
                reasons.append(f"{name}_missing")
            continue
        if left_norm != right_norm:
            reasons.append(f"{name}_mismatch")

    left_time = left.observed_at.astimezone(timezone.utc)
    right_time = right.observed_at.astimezone(timezone.utc)
    if max_age_seconds is not None:
        delta = abs((left_time - right_time).total_seconds())
        if delta > max_age_seconds:
            reasons.append("observation_time_mismatch")
    elif left_time != right_time:
        unknown = True
        reasons.append("observation_time_unspecified")

    context_fingerprint = _context_fingerprint(left, right)
    if any(code.endswith("_mismatch") for code in reasons):
        result = ComparabilityResult(
            ComparabilityState.UNCOMPARABLE,
            tuple(reasons),
            None,
            None,
            None,
            None,
            tolerance,
            context_fingerprint,
        )
        result.validate()
        return result

    if unknown and conversion is None and left.unit != right.unit:
        reasons.append("unit_conversion_missing")

    try:
        left_value, unit = left.normalized_value(conversion if left.unit != right.unit else None)
        if left.unit == right.unit:
            right_value, right_unit = float(right.value), right.unit
        else:
            if conversion is None:
                result = ComparabilityResult(
                    ComparabilityState.UNKNOWN,
                    tuple(reasons),
                    None,
                    None,
                    None,
                    None,
                    tolerance,
                    context_fingerprint,
                )
                result.validate()
                return result
            if conversion.target_unit != left.unit:
                reverse = UnitConversion(
                    source_unit=right.unit,
                    target_unit=conversion.target_unit,
                    scale=conversion.scale,
                    offset=conversion.offset,
                    revision=conversion.revision,
                )
                raise ValueError("unit conversion target must match the normalized comparison unit")
            right_value = float(right.value)
            right_unit = right.unit
    except ValueError:
        if conversion is None:
            result = ComparabilityResult(
                ComparabilityState.UNKNOWN,
                tuple(reasons + ["unit_conversion_missing"]),
                None,
                None,
                None,
                None,
                tolerance,
                context_fingerprint,
            )
            result.validate()
            return result
        raise

    if unit != right_unit:
        result = ComparabilityResult(
            ComparabilityState.UNKNOWN,
            tuple(reasons + ["unit_conversion_incompatible"]),
            None,
            None,
            None,
            None,
            tolerance,
            context_fingerprint,
        )
        result.validate()
        return result

    difference = abs(left_value - right_value)
    state = ComparabilityState.COMPARABLE if difference <= tolerance else ComparabilityState.COMPARABLE
    result = ComparabilityResult(
        state,
        tuple(reasons),
        left_value,
        right_value,
        unit,
        difference,
        tolerance,
        context_fingerprint,
    )
    result.validate()
    return result
