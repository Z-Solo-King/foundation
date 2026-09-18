from backend.performance_metrics import RegressionThreshold, evaluate_regression_gate
from benchmark.release_quality_gate import GateState, evaluate_release_quality
from benchmark.vector_scorecard import DimensionScore, QualityDimension, VectorQualityScorecard


def scorecard(*, correctness=0.90, include_latency=True):
    dims = [
        DimensionScore(QualityDimension.CORRECTNESS, correctness, baseline=0.90, max_regression=0.02, critical=True),
        DimensionScore(QualityDimension.COMPLETENESS, 0.90, baseline=0.90, max_regression=0.05, critical=True),
        DimensionScore(QualityDimension.EVIDENCE_COVERAGE, 0.90, baseline=0.90, max_regression=0.05, critical=True),
        DimensionScore(QualityDimension.CITATION_PRECISION, 0.90, baseline=0.90, max_regression=0.05, critical=False),
        DimensionScore(QualityDimension.SOURCE_INDEPENDENCE, 0.90, baseline=0.90, max_regression=0.05, critical=False),
        DimensionScore(QualityDimension.FRESHNESS, 0.90, baseline=0.90, max_regression=0.05, critical=False),
        DimensionScore(QualityDimension.RELIABILITY, 0.90, baseline=0.90, max_regression=0.05, critical=True),
        DimensionScore(QualityDimension.RESOURCE_EFFICIENCY, 0.90, baseline=0.90, max_regression=0.05, critical=False),
        DimensionScore(QualityDimension.SAFETY, 0.95, baseline=0.95, max_regression=0.02, critical=True),
    ]
    if include_latency:
        dims.append(DimensionScore(QualityDimension.LATENCY, 100, baseline=100, max_regression=20, critical=True))
    return VectorQualityScorecard(
        workload='research', population='benchmark-population', environment='ci',
        baseline_id='baseline-v1', corpus_id='research-v1', corpus_version='2026-09', dimensions=tuple(dims)
    )

def test_clean_candidate_passes_without_aggregate_score():
    gate = evaluate_release_quality(baseline=scorecard(), candidate=scorecard())
    assert gate.state is GateState.PASS
    assert gate.allowed is True
    assert gate.to_dict()['aggregate_score'] is None

def test_critical_quality_regression_blocks_release():
    baseline = scorecard(correctness=0.90)
    candidate = scorecard(correctness=0.80)
    gate = evaluate_release_quality(baseline=baseline, candidate=candidate)
    assert gate.state is GateState.BLOCKED
    assert any(item.dimension is QualityDimension.CORRECTNESS for item in gate.regressions)

def test_latency_regression_blocks_release():
    baseline = scorecard()
    candidate = scorecard()
    values = []
    for item in candidate.dimensions:
        if item.dimension is QualityDimension.LATENCY:
            values.append(DimensionScore(QualityDimension.LATENCY, 150, baseline=100, max_regression=20, critical=True))
        else:
            values.append(item)
    candidate = VectorQualityScorecard(
        workload=candidate.workload, population=candidate.population, environment=candidate.environment,
        baseline_id=candidate.baseline_id, corpus_id=candidate.corpus_id, corpus_version=candidate.corpus_version,
        dimensions=tuple(values)
    )
    gate = evaluate_release_quality(baseline=baseline, candidate=candidate)
    assert gate.state is GateState.BLOCKED
    assert any(item.dimension is QualityDimension.LATENCY for item in gate.regressions)

def test_performance_failure_blocks_without_aggregate_score():
    failure = evaluate_regression_gate(baseline=100, candidate=140, threshold=RegressionThreshold('p95_latency_ms', 0.20))
    assert failure.allowed is False
    gate = evaluate_release_quality(baseline=scorecard(), candidate=scorecard(), performance_failures=(failure,))
    assert gate.state is GateState.BLOCKED
    assert len(gate.performance_failures) == 1

def test_missing_dimension_blocks_release():
    gate = evaluate_release_quality(baseline=scorecard(), candidate=scorecard(include_latency=False))
    assert gate.state is GateState.BLOCKED
    assert QualityDimension.LATENCY in gate.missing_dimensions

def test_mismatched_corpus_identity_fails_closed():
    baseline = scorecard()
    candidate = VectorQualityScorecard(
        workload=baseline.workload, population=baseline.population, environment=baseline.environment,
        baseline_id=baseline.baseline_id, corpus_id='other', corpus_version=baseline.corpus_version,
        dimensions=baseline.dimensions
    )
    try:
        evaluate_release_quality(baseline=baseline, candidate=candidate)
    except ValueError as exc:
        assert 'corpus identity' in str(exc)
    else:
        raise AssertionError('expected corpus identity mismatch to fail closed')