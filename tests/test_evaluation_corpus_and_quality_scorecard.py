from backend.evaluation_corpus import EvaluationCase, build_corpus_manifest
from backend.quality_scorecard import (
    DIMENSIONS,
    QualityMeasurement,
    build_scorecard,
)
import pytest


def _case(case_id: str, *, replay_mode="deterministic"):
    return EvaluationCase(
        case_id=case_id,
        case_class="temporal_current",
        population="research_requests",
        expected_invariants=("freshness_gate", "provenance"),
        oracle_provenance="oracle://verified",
        replay_mode=replay_mode,
        snapshot_id="snapshot-1" if replay_mode == "snapshot" else None,
    )


def test_corpus_is_deterministic_and_order_independent():
    first = build_corpus_manifest((_case("b"), _case("a")))
    second = build_corpus_manifest((_case("a"), _case("b")))
    assert first.fingerprint == second.fingerprint
    assert len(first.fingerprint) == 64


def test_duplicate_case_ids_are_rejected():
    with pytest.raises(ValueError, match="duplicate case_id"):
        build_corpus_manifest((_case("a"), _case("a")))


def test_snapshot_cases_require_snapshot_identity():
    with pytest.raises(ValueError, match="snapshot_id"):
        EvaluationCase(
            case_id="a",
            case_class="live",
            population="p",
            expected_invariants=("x",),
            oracle_provenance="o",
            replay_mode="snapshot",
        ).validate()


def test_scorecard_preserves_missing_metrics_explicitly():
    scorecard = build_scorecard((
        QualityMeasurement("correctness", 0.95, "w", "p", "e"),
        QualityMeasurement("latency", None, "w", "p", "e", available=False, reason="not measured"),
    ))
    assert "completeness" in scorecard.missing_dimensions
    assert "latency" not in scorecard.missing_dimensions
    assert scorecard.critical_missing_dimensions == ()
    assert len(scorecard.fingerprint) == 64


def test_scorecard_rejects_duplicate_dimensions_and_null_available_values():
    with pytest.raises(ValueError, match="duplicate scorecard dimension"):
        build_scorecard((
            QualityMeasurement("correctness", 1.0, "w", "p", "e"),
            QualityMeasurement("correctness", 0.9, "w", "p", "e"),
        ))
    with pytest.raises(ValueError, match="missing available"):
        QualityMeasurement("correctness", None, "w", "p", "e").validate()


def test_receipt_metadata_binds_corpus_and_scorecard_without_authorizing_promotion():
    measurement = QualityMeasurement("correctness", True, "w", "p", "e", critical=True)
    scorecard = build_scorecard((measurement,))
    metadata = scorecard.receipt_metadata(corpus_fingerprint="a" * 64)
    assert metadata["evaluation_corpus_fingerprint"] == "a" * 64
    assert metadata["quality_scorecard_fingerprint"] == scorecard.fingerprint
    assert set(metadata["missing_dimensions"]) == set(DIMENSIONS) - {"correctness"}
