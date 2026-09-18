"""Vector quality scorecard contract without an aggregate promotion authority."""
from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
import hashlib
import json


SCHEMA = "quality-scorecard/v1"

class QualityDimension(StrEnum):
    CORRECTNESS = "correctness"
    COMPLETENESS = "completeness"
    EVIDENCE_COVERAGE = "evidence_coverage"
    CITATION_PRECISION = "citation_precision"
    SOURCE_INDEPENDENCE = "source_independence"
    FRESHNESS = "freshness"
    RELIABILITY = "reliability"
    LATENCY = "latency"
    RESOURCE_EFFICIENCY = "resource_efficiency"
    SAFETY = "safety"

_HIGHER_IS_BETTER = {
    QualityDimension.CORRECTNESS,
    QualityDimension.COMPLETENESS,
    QualityDimension.EVIDENCE_COVERAGE,
    QualityDimension.CITATION_PRECISION,
    QualityDimension.SOURCE_INDEPENDENCE,
    QualityDimension.FRESHNESS,
    QualityDimension.RELIABILITY,
    QualityDimension.RESOURCE_EFFICIENCY,
    QualityDimension.SAFETY,
}

@dataclass(frozen=True)
class DimensionScore:
    dimension: QualityDimension
    value: float | None
    baseline: float | None = None
    max_regression: float | None = None
    critical: bool = False
    source: str = "evaluation"

    def validate(self) -> None:
        if self.value is not None and not 0.0 <= self.value <= 1.0 and self.dimension is not QualityDimension.LATENCY:
            raise ValueError(f"{self.dimension.value} score must be between 0 and 1")
        if self.dimension is QualityDimension.LATENCY and self.value is not None and self.value < 0:
            raise ValueError("latency must be non-negative")
        if self.baseline is not None and self.baseline < 0:
            raise ValueError("baseline must be non-negative")
        if self.max_regression is not None and self.max_regression < 0:
            raise ValueError("max_regression must be non-negative")
        if self.source.strip() == "":
            raise ValueError("score source is required")

@dataclass(frozen=True)
class QualityRegression:
    dimension: QualityDimension
    baseline: float
    candidate: float
    allowed_regression: float

@dataclass(frozen=True)
class VectorQualityScorecard:
    workload: str
    population: str
    environment: str
    baseline_id: str
    corpus_id: str
    corpus_version: str
    dimensions: tuple[DimensionScore, ...]
    scorecard_revision: str = SCHEMA

    def validate(self) -> None:
        for name, value in (
            ("workload", self.workload),
            ("population", self.population),
            ("environment", self.environment),
            ("baseline_id", self.baseline_id),
            ("corpus_id", self.corpus_id),
            ("corpus_version", self.corpus_version),
            ("scorecard_revision", self.scorecard_revision),
        ):
            if not value.strip():
                raise ValueError(f"{name} is required")
        if not self.dimensions:
            raise ValueError("scorecard must contain dimensions")
        seen: set[QualityDimension] = set()
        for dimension in self.dimensions:
            dimension.validate()
            if dimension.dimension in seen:
                raise ValueError("duplicate quality dimension")
            seen.add(dimension.dimension)

    def missing_dimensions(self) -> tuple[QualityDimension, ...]:
        self.validate()
        return tuple(dimension for dimension in QualityDimension if dimension not in {item.dimension for item in self.dimensions})

    def critical_regressions(self) -> tuple[QualityRegression, ...]:
        self.validate()
        failures: list[QualityRegression] = []
        for item in self.dimensions:
            if item.value is None or item.baseline is None or item.max_regression is None:
                continue
            allowed = item.max_regression
            if item.dimension in _HIGHER_IS_BETTER:
                degraded_by = item.baseline - item.value
            else:
                degraded_by = item.value - item.baseline
            if item.critical and degraded_by > allowed:
                failures.append(
                    QualityRegression(item.dimension, item.baseline, item.value, allowed)
                )
        return tuple(failures)

    def digest(self) -> str:
        self.validate()
        payload = {
            "schema": SCHEMA,
            "workload": self.workload,
            "population": self.population,
            "environment": self.environment,
            "baseline_id": self.baseline_id,
            "corpus_id": self.corpus_id,
            "corpus_version": self.corpus_version,
            "scorecard_revision": self.scorecard_revision,
            "dimensions": [
                {
                    "dimension": item.dimension.value,
                    "value": item.value,
                    "baseline": item.baseline,
                    "max_regression": item.max_regression,
                    "critical": item.critical,
                    "source": item.source,
                }
                for item in sorted(self.dimensions, key=lambda value: value.dimension.value)
            ],
        }
        return hashlib.sha256(
            json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()

    def to_evaluation_receipt_context(
        self,
        *,
        candidate_commit: str,
        evaluation_receipt_ref: str | None = None,
    ) -> dict[str, object]:
        self.validate()
        if not candidate_commit.strip():
            raise ValueError("candidate_commit is required")
        return {
            "schema": "quality-scorecard-evaluation-context/v1",
            "scorecard_digest": self.digest(),
            "candidate_commit": candidate_commit,
            "baseline_id": self.baseline_id,
            "corpus_id": self.corpus_id,
            "corpus_version": self.corpus_version,
            "evaluation_receipt_ref": evaluation_receipt_ref,
            "missing_dimensions": [item.value for item in self.missing_dimensions()],
            "critical_regressions": [
                {
                    "dimension": item.dimension.value,
                    "baseline": item.baseline,
                    "candidate": item.candidate,
                    "allowed_regression": item.allowed_regression,
                }
                for item in self.critical_regressions()
            ],
            "promotion_authority": "external_evaluation_promotion_authority",
        }
