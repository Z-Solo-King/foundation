"""Independent vector quality measurements for research evaluation."""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Iterable

SCORECARD_SCHEMA = "research-quality-scorecard/v1"
DIMENSIONS = (
    "correctness",
    "completeness",
    "evidence_coverage",
    "citation_precision",
    "source_independence",
    "freshness_compliance",
    "contradiction_state",
    "reliability",
    "latency",
    "resource_efficiency",
    "safety_policy_compliance",
)


@dataclass(frozen=True)
class QualityMeasurement:
    dimension: str
    value: float | str | bool | None
    workload: str
    population: str
    environment: str
    baseline: float | None = None
    critical: bool = False
    available: bool = True
    reason: str | None = None

    def validate(self) -> None:
        if self.dimension not in DIMENSIONS:
            raise ValueError("dimension is not part of the scorecard contract")
        for name, value in (
            ("workload", self.workload),
            ("population", self.population),
            ("environment", self.environment),
        ):
            if not value.strip():
                raise ValueError(f"{name} is required")
        if not self.available and self.value is not None:
            raise ValueError("unavailable measurements must use null value")
        if self.available and self.value is None and not (self.reason or "").strip():
            raise ValueError("missing available measurements require an explicit reason")
        if self.baseline is not None and self.baseline < 0:
            raise ValueError("baseline must be non-negative")

    def to_dict(self) -> dict[str, object]:
        self.validate()
        return {
            "dimension": self.dimension,
            "value": self.value if self.available else None,
            "workload": self.workload,
            "population": self.population,
            "environment": self.environment,
            "baseline": self.baseline,
            "critical": self.critical,
            "available": self.available,
            "reason": self.reason,
        }


@dataclass(frozen=True)
class QualityScorecard:
    measurements: tuple[QualityMeasurement, ...]
    schema_version: str = SCORECARD_SCHEMA

    def validate(self) -> None:
        if self.schema_version != SCORECARD_SCHEMA:
            raise ValueError("unsupported scorecard schema")
        seen: set[str] = set()
        for measurement in self.measurements:
            measurement.validate()
            if measurement.dimension in seen:
                raise ValueError("duplicate scorecard dimension")
            seen.add(measurement.dimension)

    @property
    def missing_dimensions(self) -> tuple[str, ...]:
        self.validate()
        present = {m.dimension for m in self.measurements}
        return tuple(d for d in DIMENSIONS if d not in present)

    @property
    def critical_missing_dimensions(self) -> tuple[str, ...]:
        self.validate()
        return tuple(m.dimension for m in self.measurements if m.critical and not m.available)

    @property
    def fingerprint(self) -> str:
        self.validate()
        payload = {
            "schema_version": self.schema_version,
            "measurements": [
                m.to_dict() for m in sorted(self.measurements, key=lambda item: item.dimension)
            ],
        }
        return hashlib.sha256(
            json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
        ).hexdigest()

    def receipt_metadata(self, *, corpus_fingerprint: str) -> dict[str, object]:
        self.validate()
        if len(corpus_fingerprint) != 64:
            raise ValueError("corpus_fingerprint must be SHA-256")
        return {
            "quality_scorecard_schema": self.schema_version,
            "quality_scorecard_fingerprint": self.fingerprint,
            "evaluation_corpus_fingerprint": corpus_fingerprint,
            "missing_dimensions": list(self.missing_dimensions),
            "critical_missing_dimensions": list(self.critical_missing_dimensions),
        }


def build_scorecard(measurements: Iterable[QualityMeasurement]) -> QualityScorecard:
    scorecard = QualityScorecard(tuple(measurements))
    scorecard.validate()
    return scorecard
