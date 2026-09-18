import pytest

from backend.performance_metrics import PerformanceGateResult, RegressionThreshold, evaluate_regression_gate
from benchmark.release_quality_gate import GateState, evaluate_release_quality
from benchmark.vector_scorecard import DimensionScore, QualityDimension, VectorQualityScorecard


def scorecard(*, correctness=0.90, safety=0.95, include_latency=True):
    dimensions = [
        DimensionScore(QualityDimension.CORRECTNESS, correctness, baseline=correctness, max_regression=0.02, critical=True),
        DimensionScore(QualityDimension.SAFETY, safety, baseline=safety, max_regression=0.02, critical=True),
        DimensionScore(QualityDimension.COMPLETENESS, 0.90, baseline=0.90, max_regression=0.05, critical=True),
        DimensionScore(QualityDimension.EVIDENCE_COVERAGE, 0.90, baseline=0.90, max_regression=0.05, critical=True),
        DimensionScore(QualityDimension.CITATION_PRECISION, 0.90, baseline=0.90, max_regression=0.05, critical=False),
        DimensionScore(QualityDimension.SOURCE_INDEPENDENCE, 0.90, baseline=0.90, max_regression=0.05, critical=False),
        DimensionScore(QualityDimension.FRESHNESS, 0.90, baseline=0.90, max_regression=0.05, critical=False),
        DimensionScore(QualityDimension.RELIABILITY, 0.90, baseline=0.90, max_regression=0.05, critical=True),
        DimensionScore(QualityDimension.RESOURCE_EFFICIENCY, 0.90, baseline=0.90, max_regression=0.05, critical=False),
    ]
    if include_latency:
        dimensions.append(DimensionScore(QualityDimension.LATENCY, 100, baseline=100, max_regression=20, critical=True))
    return VectorQualityScorecard(
        workload="research",
        population="benchmark-population",
        environment="ci",
        baseline_id="baseline-v1",
        corpus_id="research-v1",
        corpus_version="2026-09",
        dimensions=tuple(dimensions),
    )


def test_clean_candidate_passes_without_aggregate_score():
    baseline = scorecard()
    candidate = scorecard()
    gate = evaluate_release_quality(baseline=baseline, candidate=candidate)
    assert gate.state is GateState.PASS
    assert gate.allowed
    assert gate.to_dict()["aggregate_score"] is None


def test_critical_quality_regression_blocks_release():
    baseline = scorecard(correctness=0.92)
    candidate = scorecard(correctness=0.80)
    gate = evaluate_release_quality(baseline=baseline, candidate=candidate)
    assert gate.state is GateState.BLOCKED
    assert any(item.dimension is QualityDimension.CORRECTNESS for item in gate.regressions)


def test_latency_regression_blocks_as_lower_is_better():
    baseline = scorecard()
    candidate = scorecard()
    dims = list(candidate.dimensions)
    index = next(i for i, item in enumerate(dims) if item.dimension is QualityDimension.LATENCY)
    dims[index] = DimensionScore(QualityDimension.LATENCY, 150, baseline=150, max_regression=20, critical=True)
    candidate = VectorQualityScorecard(
        workload=candidate.workload,
        population=candidate.population,
        environment=candidate.environment,
        baseline_id=candidate.baseline_id,
        corpus_id=candidate.corpus_id,
        corpus_version=candidate.corpus_version,
        dimensions=tuple(dims),
    )
    with pytest.raises(ValueError):
        evaluate_release_quality(baseline=baseline, candidate=candidate)


def test_performance_failure_blocks_without_mixing_into_quality_score():
    baseline = scorecard()
    candidate = scorecard()
    failure = evaluate_regression_gate(
        baseline=100,
        candidate=140,
        threshold=RegressionThreshold("p95_latency_ms", 0.20),
    )
    gate = evaluate_release_quality(
        baseline=baseline,
        candidate=candidate,
        performance_failures=(failure,),
    )
    assert gate.state is GateState.BLOCKED
    assert len(gate.performance_failures) == 1


def test_missing_dimension_blocks_release():
    baseline = scorecard()
    candidate = scorecard(include_latency=False)
    gate = evaluate_release_quality(baseline=baseline, candidate=candidate)
    assert gate.state is GateState.BLOCKED
    assert QualityDimension.LATENCY in gate.missing_dimensions


def test_mismatched_corpus_identity_fails_closed():
    baseline = scorecard()
    candidate = scorecard()
    candidate = VectorQualityScorecard(
        workload=candidate.workload,
        population=candidate.population,
        environment=candidate.environment,
        baseline_id=candidate.baseline_id,
        corpus_id="other",
        corpus_version=candidate.corpus_version,
        dimensions=candidate.dimensions,
    )
    with pytest.raises(ValueError, match="corpus identity"):
        evaluate_release_quality(baseline=baseline, candidate=candidate)
