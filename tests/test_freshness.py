from datetime import datetime, timedelta, timezone

import pytest

from backend.intelligence.freshness import (
    EvidenceTime,
    FreshnessRequirement,
    FreshnessState,
    classify_freshness,
)


NOW = datetime(2026, 9, 18, 0, 0, tzinfo=timezone.utc)


def test_current_evidence_is_fresh():
    evidence = EvidenceTime(observed_at=NOW - timedelta(minutes=5))
    result = classify_freshness(
        evidence,
        FreshnessRequirement(max_age=timedelta(hours=1)),
        now=NOW,
    )
    assert result is FreshnessState.FRESH


def test_old_evidence_is_stale():
    evidence = EvidenceTime(observed_at=NOW - timedelta(days=2))
    result = classify_freshness(
        evidence,
        FreshnessRequirement(max_age=timedelta(hours=1)),
        now=NOW,
    )
    assert result is FreshnessState.STALE


def test_missing_timestamp_is_unknown():
    result = classify_freshness(
        EvidenceTime(),
        FreshnessRequirement(max_age=timedelta(hours=1)),
        now=NOW,
    )
    assert result is FreshnessState.UNKNOWN


def test_future_dated_content_is_explicit():
    result = classify_freshness(
        EvidenceTime(published_at=NOW + timedelta(minutes=1)),
        FreshnessRequirement(max_age=timedelta(hours=1)),
        now=NOW,
    )
    assert result is FreshnessState.FUTURE


def test_naive_timestamp_rejected():
    with pytest.raises(ValueError, match="timezone-aware"):
        classify_freshness(
            EvidenceTime(observed_at=datetime(2026, 9, 18)),
            FreshnessRequirement(),
            now=NOW,
        )


def test_non_strict_requirement_allows_unknown_timestamp():
    result = classify_freshness(
        EvidenceTime(),
        FreshnessRequirement(max_age=None, require_timestamp=False),
        now=NOW,
    )
    assert result is FreshnessState.FRESH


def test_negative_freshness_requirement_is_rejected():
    with pytest.raises(ValueError, match="max_age"):
        FreshnessRequirement(max_age=timedelta(seconds=-1)).validate()


def test_observed_timestamp_wins_over_published_timestamp():
    evidence = EvidenceTime(
        observed_at=NOW - timedelta(minutes=5),
        published_at=NOW - timedelta(days=2),
    )
    result = classify_freshness(
        evidence,
        FreshnessRequirement(max_age=timedelta(hours=1)),
        now=NOW,
    )
    assert result is FreshnessState.FRESH


def test_published_timestamp_can_satisfy_unbounded_freshness():
    evidence = EvidenceTime(published_at=NOW - timedelta(days=2))
    result = classify_freshness(
        evidence,
        FreshnessRequirement(max_age=None),
        now=NOW,
    )
    assert result is FreshnessState.FRESH



def test_observed_timestamp_with_unbounded_freshness_is_fresh():
    result = classify_freshness(
        EvidenceTime(observed_at=NOW - timedelta(days=30)),
        FreshnessRequirement(max_age=None),
        now=NOW,
    )
    assert result is FreshnessState.FRESH
