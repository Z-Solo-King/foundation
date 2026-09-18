"""Deterministic citation-precision sampling and human review contract.

Sample selection is reproducible from recorded research-output identities. Semantic
support is never inferred by this module: a reviewer records supported, unsupported,
or unresolved outcomes and the metric is derived only from resolved reviews.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import StrEnum
from hashlib import sha256
from typing import Iterable


SCHEMA = "citation-precision-sampling/v1"
MAX_OUTPUTS = 10_000
MAX_CITATIONS_PER_OUTPUT = 256
MAX_SAMPLES = 1_024


class ReviewOutcome(StrEnum):
    SUPPORTED = "supported"
    UNSUPPORTED = "unsupported"
    UNRESOLVED = "unresolved"


@dataclass(frozen=True)
class CitationRef:
    citation_id: str
    claim: str
    source_url: str
    observation_id: str
    span_text: str = ""

    def validate(self) -> None:
        for name, value in (
            ("citation_id", self.citation_id),
            ("claim", self.claim),
            ("source_url", self.source_url),
            ("observation_id", self.observation_id),
        ):
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} is required")


@dataclass(frozen=True)
class ResearchOutputSample:
    output_id: str
    generated_at: datetime
    citations: tuple[CitationRef, ...]
    execution_digest: str = ""

    def validate(self) -> None:
        if not self.output_id.strip():
            raise ValueError("output_id is required")
        if self.generated_at.tzinfo is None or self.generated_at.utcoffset() is None:
            raise ValueError("generated_at must be timezone-aware")
        if len(self.citations) > MAX_CITATIONS_PER_OUTPUT:
            raise ValueError("citation count exceeds safety limit")
        seen: set[str] = set()
        for citation in self.citations:
            citation.validate()
            if citation.citation_id in seen:
                raise ValueError("citation IDs must be unique")
            seen.add(citation.citation_id)


@dataclass(frozen=True)
class CitationReview:
    citation_id: str
    output_id: str
    reviewed_at: datetime
    outcome: ReviewOutcome
    reviewer_id: str
    note_digest: str = ""

    def validate(self) -> None:
        if not self.citation_id.strip() or not self.output_id.strip():
            raise ValueError("review citation/output identity is required")
        if self.reviewed_at.tzinfo is None or self.reviewed_at.utcoffset() is None:
            raise ValueError("reviewed_at must be timezone-aware")
        if not self.reviewer_id.strip():
            raise ValueError("reviewer_id is required")
        if self.note_digest and len(self.note_digest) != 64:
            raise ValueError("note_digest must be a SHA-256 digest when supplied")


@dataclass(frozen=True)
class CitationSample:
    output_id: str
    citation_id: str
    rank: int

    def validate(self) -> None:
        if not self.output_id.strip() or not self.citation_id.strip():
            raise ValueError("sample identity is required")
        if self.rank < 0:
            raise ValueError("sample rank must be non-negative")


@dataclass(frozen=True)
class CitationPrecisionMetric:
    window_start: datetime
    window_end: datetime
    sampled_citations: int
    supported: int
    unsupported: int
    unresolved: int

    @property
    def resolved(self) -> int:
        return self.supported + self.unsupported

    @property
    def precision(self) -> float | None:
        if self.resolved == 0:
            return None
        return self.supported / self.resolved

    def validate(self) -> None:
        if self.window_start.tzinfo is None or self.window_start.utcoffset() is None:
            raise ValueError("window_start must be timezone-aware")
        if self.window_end.tzinfo is None or self.window_end.utcoffset() is None:
            raise ValueError("window_end must be timezone-aware")
        if self.window_end < self.window_start:
            raise ValueError("window_end must not precede window_start")
        values = (
            self.sampled_citations,
            self.supported,
            self.unsupported,
            self.unresolved,
        )
        if any(value < 0 for value in values):
            raise ValueError("precision counts must be non-negative")
        if self.supported + self.unsupported + self.unresolved != self.sampled_citations:
            raise ValueError("precision counts must sum to sampled citations")

    def to_dict(self) -> dict[str, object]:
        self.validate()
        return {
            "schema": SCHEMA,
            "window_start": self.window_start.isoformat(),
            "window_end": self.window_end.isoformat(),
            "sampled_citations": self.sampled_citations,
            "supported": self.supported,
            "unsupported": self.unsupported,
            "unresolved": self.unresolved,
            "resolved": self.resolved,
            "precision": self.precision,
        }


def _priority(output_id: str, citation_id: str) -> str:
    return sha256(f"{output_id}\x00{citation_id}".encode("utf-8")).hexdigest()


def select_citation_samples(
    outputs: Iterable[ResearchOutputSample],
    *,
    max_outputs: int,
    max_citations: int,
    window_start: datetime | None = None,
    window_end: datetime | None = None,
) -> tuple[CitationSample, ...]:
    if not 1 <= max_outputs <= MAX_OUTPUTS:
        raise ValueError("max_outputs is outside safety limit")
    if not 1 <= max_citations <= MAX_SAMPLES:
        raise ValueError("max_citations is outside safety limit")
    if window_start is not None and (window_start.tzinfo is None or window_start.utcoffset() is None):
        raise ValueError("window_start must be timezone-aware")
    if window_end is not None and (window_end.tzinfo is None or window_end.utcoffset() is None):
        raise ValueError("window_end must be timezone-aware")
    if window_start is not None and window_end is not None and window_end < window_start:
        raise ValueError("window_end must not precede window_start")

    materialized = tuple(outputs)
    if len(materialized) > MAX_OUTPUTS:
        raise ValueError("output count exceeds safety limit")

    eligible: list[ResearchOutputSample] = []
    seen_outputs: set[str] = set()
    for output in materialized:
        output.validate()
        if output.output_id in seen_outputs:
            raise ValueError("output IDs must be unique")
        seen_outputs.add(output.output_id)
        if window_start is not None and output.generated_at < window_start:
            continue
        if window_end is not None and output.generated_at > window_end:
            continue
        eligible.append(output)

    eligible.sort(key=lambda item: (item.generated_at, item.output_id), reverse=True)
    chosen_outputs = eligible[:max_outputs]

    candidates = [
        (output, citation)
        for output in chosen_outputs
        for citation in output.citations
    ]
    candidates.sort(key=lambda pair: _priority(pair[0].output_id, pair[1].citation_id))
    candidates = candidates[:max_citations]

    samples = [
        CitationSample(output.output_id, citation.citation_id, rank)
        for rank, (output, citation) in enumerate(candidates)
    ]
    for sample in samples:
        sample.validate()
    return tuple(samples)


def build_precision_metric(
    samples: Iterable[CitationSample],
    reviews: Iterable[CitationReview],
    *,
    window_start: datetime,
    window_end: datetime,
) -> CitationPrecisionMetric:
    if window_start.tzinfo is None or window_start.utcoffset() is None:
        raise ValueError("window_start must be timezone-aware")
    if window_end.tzinfo is None or window_end.utcoffset() is None:
        raise ValueError("window_end must be timezone-aware")
    if window_end < window_start:
        raise ValueError("window_end must not precede window_start")

    materialized_samples = tuple(samples)
    if len(materialized_samples) > MAX_SAMPLES:
        raise ValueError("sample count exceeds safety limit")
    sample_keys: set[tuple[str, str]] = set()
    for sample in materialized_samples:
        sample.validate()
        key = (sample.output_id, sample.citation_id)
        if key in sample_keys:
            raise ValueError("sample contains duplicate citation identity")
        sample_keys.add(key)

    by_key: dict[tuple[str, str], CitationReview] = {}
    for review in reviews:
        review.validate()
        if review.reviewed_at < window_start or review.reviewed_at > window_end:
            continue
        key = (review.output_id, review.citation_id)
        if key not in sample_keys:
            continue
        if key in by_key:
            raise ValueError("multiple reviews exist for one sampled citation")
        by_key[key] = review

    supported = sum(review.outcome is ReviewOutcome.SUPPORTED for review in by_key.values())
    unsupported = sum(review.outcome is ReviewOutcome.UNSUPPORTED for review in by_key.values())
    unresolved = len(materialized_samples) - supported - unsupported

    metric = CitationPrecisionMetric(
        window_start=window_start,
        window_end=window_end,
        sampled_citations=len(materialized_samples),
        supported=supported,
        unsupported=unsupported,
        unresolved=unresolved,
    )
    metric.validate()
    return metric


def metric_now() -> datetime:
    return datetime.now(timezone.utc)
