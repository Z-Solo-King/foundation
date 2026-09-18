"""Deterministic measurement comparability metadata.

This module classifies evidence conditions only; it does not verify claims or
authorize publication/promotion.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from decimal import Decimal
from typing import NamedTuple


COMPARABILITY_SCHEMA = "measurement-comparability/v1"


class ComparabilityState(StrEnum):
    COMPARABLE = "comparable"
    PARTIAL = "partial"
    UNCOMPARABLE = "uncomparable"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class MeasurementContext:
    entity: str
    variant: str | None = None
    region: str | None = None
    environment: str | None = None
    software_revision: str | None = None
    methodology: str | None = None
    tool_version: str | None = None
    workload: str | None = None
    population: str | None = None
    sample_size: int | None = None
    unit: str | None = None
    uncertainty_low: Decimal | None = None
    uncertainty_high: Decimal | None = None
    replication_count: int | None = None
    provenance_id: str = ""

    def validate(self) -> None:
        if not self.entity.strip() or not self.provenance_id.strip():
            raise ValueError("entity and provenance_id are required")
        if self.sample_size is not None and self.sample_size < 1:
            raise ValueError("sample_size must be positive")
        if self.replication_count is not None and self.replication_count < 1:
            raise ValueError("replication_count must be positive")
        if self.uncertainty_low is not None and self.uncertainty_high is not None:
            if self.uncertainty_high < self.uncertainty_low:
                raise ValueError("uncertainty_high must not precede uncertainty_low")


@dataclass(frozen=True)
class Measurement:
    value: Decimal
    context: MeasurementContext

    def validate(self) -> None:
        self.context.validate()


class NormalizedMeasurement(NamedTuple):
    value: Decimal
    dimension: str
    unit: str


_UNITS: dict[str, tuple[str, Decimal]] = {
    "ms": ("time", Decimal("1")),
    "s": ("time", Decimal("1000")),
    "us": ("time", Decimal("0.001")),
    "bytes": ("bytes", Decimal("1")),
    "kb": ("bytes", Decimal("1024")),
    "mb": ("bytes", Decimal("1048576")),
    "g": ("mass", Decimal("1")),
    "kg": ("mass", Decimal("1000")),
    "mg": ("mass", Decimal("0.001")),
}


def normalize_measurement(value: Decimal, unit: str | None) -> NormalizedMeasurement | None:
    if not unit:
        return None
    spec = _UNITS.get(unit.strip().casefold())
    if spec is None:
        return None
    dimension, factor = spec
    return NormalizedMeasurement(value * factor, dimension, unit.strip().casefold())


@dataclass(frozen=True)
class ComparabilityResult:
    state: ComparabilityState
    reasons: tuple[str, ...]
    normalized_delta: Decimal | None = None
    schema_version: str = COMPARABILITY_SCHEMA

    def validate(self) -> None:
        if self.schema_version != COMPARABILITY_SCHEMA:
            raise ValueError("unsupported comparability schema")


def classify_comparability(left: Measurement, right: Measurement) -> ComparabilityResult:
    left.validate()
    right.validate()
    reasons: list[str] = []
    for field in ("variant", "region", "environment", "software_revision", "methodology", "tool_version", "workload", "population"):
        a = getattr(left.context, field)
        b = getattr(right.context, field)
        if a is None or b is None:
            reasons.append(f"missing:{field}")
        elif a.casefold() != b.casefold():
            reasons.append(f"different:{field}")

    if left.context.entity.casefold() != right.context.entity.casefold():
        return ComparabilityResult(ComparabilityState.UNCOMPARABLE, ("different:entity",))
    if any(reason.startswith("different:") for reason in reasons):
        return ComparabilityResult(ComparabilityState.UNCOMPARABLE, tuple(sorted(reasons)))

    lnorm = normalize_measurement(left.value, left.context.unit)
    rnorm = normalize_measurement(right.value, right.context.unit)
    if lnorm is None or rnorm is None:
        return ComparabilityResult(ComparabilityState.UNKNOWN, tuple(sorted(set(reasons + ["unknown:unit"]))))

    if lnorm.dimension != rnorm.dimension:
        return ComparabilityResult(ComparabilityState.UNCOMPARABLE, ("different:unit_dimension",))

    state = ComparabilityState.PARTIAL if reasons else ComparabilityState.COMPARABLE
    return ComparabilityResult(state, tuple(sorted(set(reasons))), abs(lnorm.value - rnorm.value))


def test_measurement_context_accepts_ordered_uncertainty_range():
    MeasurementContext(
        entity="cpu",
        provenance_id="src",
        uncertainty_low=Decimal("1"),
        uncertainty_high=Decimal("2"),
    ).validate()


def test_comparability_result_accepts_canonical_schema():
    from backend.intelligence.comparability import ComparabilityResult
    ComparabilityResult(ComparabilityState.COMPARABLE, ()).validate()
