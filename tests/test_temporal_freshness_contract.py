from datetime import datetime, timedelta, timezone

from backend.intelligence.freshness import (
    EvidenceTime,
    FreshnessRequirement,
    FreshnessState,
    TimestampQuality,
    cache_reuse_allowed,
    classify_freshness,
)


NOW = datetime(2026, 9, 18, 0, 0, tzinfo=timezone.utc)


def test_historical_question_can_use_old_evidence_within_effective_scope():
    evidence = EvidenceTime(
        published_at=NOW - timedelta(days=365),
        effective_from=NOW - timedelta(days=400),
        effective_to=NOW - timedelta(days=300),
        timestamp_quality=TimestampQuality.PRECISE,
    )
    result = classify_freshness(
        evidence,
        FreshnessRequirement(historical=True, as_of=NOW - timedelta(days=350)),
        now=NOW,
    )
    assert result is FreshnessState.FRESH


def test_current_request_rejects_expired_effective_scope():
    evidence = EvidenceTime(
        published_at=NOW - timedelta(days=2),
        effective_to=NOW - timedelta(hours=1),
    )
    assert classify_freshness(
        evidence,
        FreshnessRequirement(max_age=timedelta(days=7)),
        now=NOW,
    ) is FreshnessState.STALE


def test_current_request_marks_future_effective_document_future():
    evidence = EvidenceTime(
        published_at=NOW,
        effective_from=NOW + timedelta(hours=1),
    )
    assert classify_freshness(evidence, FreshnessRequirement(max_age=timedelta(days=1)), now=NOW) is FreshnessState.FUTURE


def test_cache_reuse_requires_fresh_state():
    evidence = EvidenceTime(published_at=NOW - timedelta(hours=2))
    requirement = FreshnessRequirement(max_age=timedelta(hours=1))
    assert cache_reuse_allowed(evidence, requirement, now=NOW) is False


def test_timezone_normalization_is_deterministic():
    evidence = EvidenceTime(published_at=datetime(2026, 9, 17, 20, 0, tzinfo=timezone(timedelta(hours=-4))))
    assert classify_freshness(
        evidence,
        FreshnessRequirement(max_age=timedelta(hours=2)),
        now=NOW,
    ) is FreshnessState.FRESH


def test_unknown_timestamp_does_not_become_fresh_for_current_state():
    assert classify_freshness(
        EvidenceTime(timestamp_quality=TimestampQuality.MISSING),
        FreshnessRequirement(max_age=timedelta(days=1)),
        now=NOW,
    ) is FreshnessState.UNKNOWN
