from dataclasses import replace

import pytest

from backend.evaluation.integrity_metrics import (
    IntegrityObservation,
    TrustTier,
    calculate_integrity_metrics,
)


def test_integrity_metrics_cover_concentration_temporal_disagreement_and_ugc():
    observations = (
        IntegrityObservation("e1", "origin-a", "family-a", TrustTier.PRIMARY, 10, 20, True),
        IntegrityObservation("e2", "origin-a", "family-a", TrustTier.UGC, 15, 20, True),
        IntegrityObservation("e3", "origin-b", "family-b", TrustTier.COMMUNITY, 10, 20, False),
    )
    metrics = calculate_integrity_metrics(observations)
    assert metrics.sample_count == 3
    assert 0 <= metrics.retrieval_concentration <= 1
    assert 0 <= metrics.origin_family_concentration <= 1
    assert metrics.temporal_anomaly_rate == 0.0
    assert metrics.disagreement_rate == pytest.approx(1 / 3)
    assert metrics.ugc_ratio == pytest.approx(1 / 3)


def test_temporal_anomaly_and_zero_sample_paths():
    anomalous = IntegrityObservation("e1", "o1", "f1", TrustTier.UNKNOWN, 30, 20, None)
    metrics = calculate_integrity_metrics((replace(anomalous, published_at=None), anomalous))
    assert metrics.temporal_anomaly_rate == 1.0
    assert calculate_integrity_metrics(()).sample_count == 0


def test_integrity_observation_fail_closed_guards():
    with pytest.raises(ValueError):
        replace(IntegrityObservation("e", "o", "f"), origin_id="").validate()
    with pytest.raises(ValueError):
        replace(IntegrityObservation("e", "o", "f"), published_at=-1).validate()
    with pytest.raises(ValueError):
        IntegrityObservation("e", "o", "f", trust_tier="ugc").validate()


def test_many_unique_origins_have_low_concentration_and_single_origin_is_maximal():
    many = tuple(IntegrityObservation(str(i), f"origin-{i}", f"family-{i}") for i in range(5))
    assert calculate_integrity_metrics(many).retrieval_concentration == 0.0
    assert calculate_integrity_metrics((IntegrityObservation("e", "o", "f"),)).retrieval_concentration == 1.0