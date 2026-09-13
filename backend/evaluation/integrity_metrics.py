"""Deterministic integrity metrics for poisoning and evidence-concentration detection."""
from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from math import fsum
from typing import Sequence


class TrustTier(StrEnum):
    PRIMARY = "primary"
    ESTABLISHED = "established"
    COMMUNITY = "community"
    UGC = "ugc"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class IntegrityObservation:
    evidence_id: str
    origin_id: str
    source_family_id: str
    trust_tier: TrustTier = TrustTier.UNKNOWN
    published_at: float | None = None
    observed_at: float | None = None
    supports_claim: bool | None = None
    content_fingerprint: str | None = None

    def validate(self) -> None:
        for name in ("evidence_id", "origin_id", "source_family_id"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must not be empty")
        if not isinstance(self.trust_tier, TrustTier):
            raise ValueError("trust_tier must be a TrustTier")
        for name in ("published_at", "observed_at"):
            value = getattr(self, name)
            if value is not None and value < 0:
                raise ValueError(f"{name} must be non-negative")


@dataclass(frozen=True)
class IntegrityMetrics:
    retrieval_concentration: float
    origin_family_concentration: float
    temporal_anomaly_rate: float
    disagreement_rate: float
    ugc_ratio: float
    sample_count: int

    def validate(self) -> None:
        for name in (
            "retrieval_concentration", "origin_family_concentration", "temporal_anomaly_rate",
            "disagreement_rate", "ugc_ratio",
        ):
            value = getattr(self, name)
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be between 0 and 1")
        if self.sample_count < 0:
            raise ValueError("sample_count must be non-negative")


def _hhi(values: Sequence[str]) -> float:
    if not values:
        return 0.0
    counts: dict[str, int] = {}
    for value in values:
        counts[value] = counts.get(value, 0) + 1
    total = len(values)
    return fsum((count / total) ** 2 for count in counts.values())


def _concentration(values: Sequence[str]) -> float:
    if not values:
        return 0.0
    hhi = _hhi(values)
    minimum = 1.0 / len(set(values))
    if minimum >= 1.0:
        return 1.0
    score = (hhi - minimum) / (1.0 - minimum)
    return 0.0 if abs(score) < 1e-12 else min(1.0, max(0.0, score))


def calculate_integrity_metrics(observations: Sequence[IntegrityObservation]) -> IntegrityMetrics:
    for observation in observations:
        observation.validate()
    if not observations:
        return IntegrityMetrics(0.0, 0.0, 0.0, 0.0, 0.0, 0)

    origins = [observation.origin_id for observation in observations]
    families = [observation.source_family_id for observation in observations]
    temporal_total = sum(
        observation.published_at is not None and observation.observed_at is not None
        for observation in observations
    )
    temporal_anomalies = sum(
        observation.published_at is not None
        and observation.observed_at is not None
        and observation.published_at > observation.observed_at
        for observation in observations
    )
    disagreements = [observation for observation in observations if observation.supports_claim is not None]
    support_count = sum(bool(observation.supports_claim) for observation in disagreements)
    disagreement_rate = 0.0
    if len(disagreements) >= 2:
        disagreement_rate = min(support_count, len(disagreements) - support_count) / len(disagreements)

    ugc_count = sum(observation.trust_tier is TrustTier.UGC for observation in observations)
    result = IntegrityMetrics(
        retrieval_concentration=_concentration(origins),
        origin_family_concentration=_concentration(families),
        temporal_anomaly_rate=(temporal_anomalies / temporal_total) if temporal_total else 0.0,
        disagreement_rate=disagreement_rate,
        ugc_ratio=ugc_count / len(observations),
        sample_count=len(observations),
    )
    result.validate()
    return result


__all__ = ["TrustTier", "IntegrityObservation", "IntegrityMetrics", "calculate_integrity_metrics"]