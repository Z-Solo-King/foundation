"""Tests for evaluation harness."""

import pytest
from backend.evaluation.harness import (
    EvaluationHarness,
    BenchmarkCase,
    EvaluationResult,
    EvaluationCategory,
)
from backend.evaluation.bootstrap import create_bootstrap_corpus


def test_register_case():
    """Benchmark case can be registered."""
    harness = EvaluationHarness()
    case = BenchmarkCase(
        case_id="test-1",
        category=EvaluationCategory.RETRIEVAL,
        description="Test case",
        input_question="What is X?",
        expected_output={"answer": "Y"},
    )
    harness.register_case(case)
    assert len(harness._cases) == 1


def test_duplicate_case_rejected():
    """Duplicate case ID is rejected."""
    harness = EvaluationHarness()
    case1 = BenchmarkCase(
        case_id="test-1",
        category=EvaluationCategory.RETRIEVAL,
        description="Test",
        input_question="?",
        expected_output={},
    )
    harness.register_case(case1)
    
    case2 = BenchmarkCase(
        case_id="test-1",  # Same ID
        category=EvaluationCategory.RETRIEVAL,
        description="Test",
        input_question="?",
        expected_output={},
    )
    
    with pytest.raises(ValueError, match="already registered"):
        harness.register_case(case2)


def test_record_result():
    """Results can be recorded for cases."""
    harness = EvaluationHarness()
    case = BenchmarkCase(
        case_id="test-1",
        category=EvaluationCategory.RETRIEVAL,
        description="Test",
        input_question="?",
        expected_output={},
    )
    harness.register_case(case)
    
    result = EvaluationResult(
        case_id="test-1",
        passed=True,
        latency_ms=50.0,
    )
    harness.record_result("test-1", result)
    
    assert len(harness._results["test-1"]) == 1
    assert harness._results["test-1"][0].passed is True


def test_summary_by_category():
    """Summary groups results by category."""
    harness = EvaluationHarness()
    
    case1 = BenchmarkCase(
        case_id="ret-1",
        category=EvaluationCategory.RETRIEVAL,
        description="R1",
        input_question="?",
        expected_output={},
    )
    case2 = BenchmarkCase(
        case_id="ext-1",
        category=EvaluationCategory.EXTRACTION,
        description="E1",
        input_question="?",
        expected_output={},
    )
    harness.register_case(case1)
    harness.register_case(case2)
    
    harness.record_result("ret-1", EvaluationResult("ret-1", passed=True))
    harness.record_result("ext-1", EvaluationResult("ext-1", passed=False))
    
    summary = harness.summary_by_category()
    assert summary["retrieval"]["passed"] == 1
    assert summary["extraction"]["passed"] == 0


def test_bootstrap_readiness():
    """Bootstrap gate requires 50 cases at 95% pass rate."""
    harness = EvaluationHarness()
    
    # Not enough cases yet
    is_ready, reason = harness.bootstrap_readiness()
    assert is_ready is False
    
    # Create 50 cases
    for i in range(50):
        case = BenchmarkCase(
            case_id=f"case-{i}",
            category=EvaluationCategory.RETRIEVAL,
            description=f"Case {i}",
            input_question="?",
            expected_output={},
        )
        harness.register_case(case)
        harness.record_result(f"case-{i}", EvaluationResult(f"case-{i}", passed=True))
    
    is_ready, reason = harness.bootstrap_readiness()
    assert is_ready is True


def test_production_readiness():
    """Production gate requires 150+ cases and category coverage."""
    harness = EvaluationHarness()
    
    # Not enough cases
    is_ready, reason = harness.production_readiness()
    assert is_ready is False
    
    # Create 150 cases with category distribution
    categories = list(EvaluationCategory)
    cases_per_cat = 150 // len(categories)
    
    for i in range(150):
        cat = categories[i % len(categories)]
        case = BenchmarkCase(
            case_id=f"case-{i}",
            category=cat,
            description=f"Case {i}",
            input_question="?",
            expected_output={},
        )
        harness.register_case(case)
        harness.record_result(f"case-{i}", EvaluationResult(f"case-{i}", passed=True))
    
    is_ready, reason = harness.production_readiness()
    assert is_ready is True


def test_bootstrap_corpus_has_50_cases():
    """Bootstrap corpus contains 50 cases."""
    corpus = create_bootstrap_corpus()
    assert len(corpus) == 50
    
    # Check distribution across categories
    by_cat = {}
    for case in corpus:
        by_cat[case.category] = by_cat.get(case.category, 0) + 1
    
    # Should have cases in multiple categories
    assert len(by_cat) > 1
