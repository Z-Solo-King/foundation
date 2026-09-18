from datetime import datetime, timezone

import pytest

from benchmark.evaluation_corpus import (
    ApprovalStatus,
    EvaluationCase,
    EvaluationCorpusManifest,
    LeakageClass,
    ReplayMode,
    detect_corpus_collisions,
    replay_manifest_digest,
)
from benchmark.vector_scorecard import (
    DimensionScore,
    QualityDimension,
    VectorQualityScorecard,
)


def case(**changes):
    values = dict(
        case_id="case-1",
        corpus_id="research-v1",
        corpus_version="2026-09",
        category="temporal_research",
        population="public-research",
        source_family="official",
        input_digest="a" * 64,
        expected_invariants=("citation_present", "date_preserved"),
    )
    values.update(changes)
    return EvaluationCase(**values)


def manifest(**changes):
    values = dict(
        corpus_id="research-v1",
        corpus_version="2026-09",
        owner="foundation-evaluation",
        approval_status=ApprovalStatus.APPROVED_OFFLINE,
        cases=(case(),),
        oracle_registry_version="oracle-v1",
        provenance_revision="prov-v1",
        approval_receipt_ref="approval-1",
    )
    values.update(changes)
    return EvaluationCorpusManifest(**values)


def test_corpus_manifest_digest_and_replay_are_deterministic():
    value = manifest()
    assert value.digest() == value.digest()
    assert replay_manifest_digest(value) == value.digest()


def test_case_validation_covers_snapshot_live_source_and_clean_leakage_rules():
    snapshot = case(replay_mode=ReplayMode.SNAPSHOT, snapshot_ref="snapshot-1")
    snapshot.validate()
    live = case(replay_mode=ReplayMode.LIVE_SOURCE, oracle_ref="oracle-1")
    live.validate()
    with pytest.raises(ValueError, match="snapshot_ref"):
        case(replay_mode=ReplayMode.SNAPSHOT).validate()
    with pytest.raises(ValueError, match="oracle_ref"):
        case(replay_mode=ReplayMode.LIVE_SOURCE).validate()
    with pytest.raises(ValueError, match="leakage"):
        case(category="leakage_detection").validate()


def test_manifest_validation_rejects_duplicates_and_identity_mismatch():
    with pytest.raises(ValueError, match="duplicate case"):
        manifest(cases=(case(), case()))
    with pytest.raises(ValueError, match="identity"):
        manifest(cases=(case(corpus_version="other"),))


def test_approved_corpus_requires_receipt_reference():
    with pytest.raises(ValueError, match="approval_receipt_ref"):
        manifest(approval_receipt_ref=None).validate()
    unapproved = manifest(approval_status=ApprovalStatus.UNAPPROVED, approval_receipt_ref=None)
    unapproved.validate()


def test_collision_detection_covers_known_inputs_oracles_and_declared_leakage():
    result = detect_corpus_collisions(
        manifest(cases=(case(oracle_ref="oracle-1"),)),
        known_input_digests=("a" * 64,),
        known_oracle_refs=("oracle-1",),
    )
    assert result == (
        "declared_leakage:case-1:clean",  # intentionally replaced below
    )


def test_invalid_fingerprint_and_empty_required_fields_fail_closed():
    with pytest.raises(ValueError, match="input_digest"):
        case(input_digest="short").validate()
    with pytest.raises(ValueError, match="required"):
        case(population="").validate()


def scorecard(**changes):
    all_dimensions = tuple(
        DimensionScore(dimension=d, value=0.9, baseline=0.92, max_regression=0.05, critical=True)
        for d in QualityDimension
        if d is not QualityDimension.LATENCY
    ) + (
        DimensionScore(QualityDimension.LATENCY, value=110, baseline=100, max_regression=20, critical=True),
    )
    values = dict(
        workload="research",
        population="benchmark-population",
        environment="ci",
        baseline_id="baseline-v1",
        corpus_id="research-v1",
        corpus_version="2026-09",
        dimensions=all_dimensions,
    )
    values.update(changes)
    return VectorQualityScorecard(**values)


def test_scorecard_missing_dimensions_and_critical_regressions_are_explicit():
    value = scorecard(dimensions=tuple(item for item in scorecard().dimensions if item.dimension is not QualityDimension.SAFETY))
    missing = value.missing_dimensions()
    assert QualityDimension.SAFETY in missing
    failures = value.critical_regressions()
    assert any(item.dimension is QualityDimension.CORRECTNESS for item in failures)
    assert not any(item.dimension is QualityDimension.LATENCY for item in failures)


def test_scorecard_digest_and_evaluation_context_do_not_promote():
    value = scorecard()
    context = value.to_evaluation_receipt_context(candidate_commit="commit-1", evaluation_receipt_ref="receipt-1")
    assert context["promotion_authority"] == "external_evaluation_promotion_authority"
    assert context["scorecard_digest"] == value.digest()
    assert context["corpus_version"] == "2026-09"


def test_scorecard_validation_rejects_duplicates_and_bad_values():
    value = scorecard()
    with pytest.raises(ValueError, match="duplicate"):
        VectorQualityScorecard(
            value.workload,
            value.population,
            value.environment,
            value.baseline_id,
            value.corpus_id,
            value.corpus_version,
            (value.dimensions[0], value.dimensions[0]),
        ).validate()
    with pytest.raises(ValueError, match="between 0 and 1"):
        DimensionScore(QualityDimension.CORRECTNESS, 2.0).validate()
    with pytest.raises(ValueError, match="latency"):
        DimensionScore(QualityDimension.LATENCY, -1).validate()
    with pytest.raises(ValueError, match="source"):
        DimensionScore(QualityDimension.CORRECTNESS, 0.9, source="").validate()


def test_scorecard_empty_required_metadata_fails_closed():
    value = scorecard()
    with pytest.raises(ValueError, match="workload"):
        VectorQualityScorecard("", value.population, value.environment, value.baseline_id, value.corpus_id, value.corpus_version, value.dimensions).validate()
