"""Evaluation harness for regression testing and benchmark promotion.

Bootstrap benchmark: 50 representative cases.
Production gate: 150-300 cases before promotion.
Continuous adversarial testing.
"""

from dataclasses import dataclass
from enum import StrEnum
from typing import Any


class EvaluationCategory(StrEnum):
    RETRIEVAL = "retrieval"
    EXTRACTION = "extraction"
    CONTRADICTION = "contradiction"
    TEMPORAL = "temporal"
    INDEPENDENCE = "independence"
    CITATION = "citation"
    FRESHNESS = "freshness"
    RESOURCE = "resource"
    SECURITY = "security"
    ARCHITECTURE = "architecture"


@dataclass(frozen=True)
class BenchmarkCase:
    """Single benchmark case."""
    case_id: str
    category: EvaluationCategory
    description: str
    input_question: str
    expected_output: Any
    adversarial_aspect: str | None = None  # What this case targets
    difficulty: str = "normal"  # easy, normal, hard, extreme


@dataclass(frozen=True)
class EvaluationResult:
    """Result of evaluating a single case."""
    case_id: str
    passed: bool
    metric_value: float | None = None  # Custom metric if applicable
    error: str | None = None
    latency_ms: float | None = None
    notes: str = ""


class EvaluationHarness:
    """Runs benchmark suite and tracks promotion readiness."""
    
    def __init__(self):
        self._cases: list[BenchmarkCase] = []
        self._results: dict[str, list[EvaluationResult]] = {}  # case_id -> [results]
        self._promotion_threshold = 0.95  # 95% pass rate
        self._bootstrap_target = 50
        self._production_target = 150
    
    def register_case(self, case: BenchmarkCase) -> None:
        """Register a benchmark case."""
        if any(c.case_id == case.case_id for c in self._cases):
            raise ValueError(f"case {case.case_id} already registered")
        self._cases.append(case)
    
    def record_result(self, case_id: str, result: EvaluationResult) -> None:
        """Record evaluation result for a case."""
        if not any(c.case_id == case_id for c in self._cases):
            raise ValueError(f"case {case_id} not registered")
        if case_id not in self._results:
            self._results[case_id] = []
        self._results[case_id].append(result)
    
    def summary_by_category(self) -> dict[str, dict[str, Any]]:
        """Get summary statistics by category.
        
        Returns:
            Dict: {category -> {passed: int, total: int, pass_rate: float}}
        """
        by_cat = {cat: {"passed": 0, "total": 0} for cat in EvaluationCategory}
        
        for case in self._cases:
            by_cat[case.category]["total"] += 1
            
            if case.case_id in self._results and self._results[case.case_id]:
                latest = self._results[case.case_id][-1]
                if latest.passed:
                    by_cat[case.category]["passed"] += 1
        
        # Compute pass rates
        summary = {}
        for cat, counts in by_cat.items():
            total = counts["total"]
            passed = counts["passed"]
            pass_rate = passed / total if total > 0 else 0.0
            summary[str(cat)] = {
                "passed": passed,
                "total": total,
                "pass_rate": pass_rate,
            }
        
        return summary
    
    def bootstrap_readiness(self) -> tuple[bool, str]:
        """Check if bootstrap benchmark gate is met.
        
        Returns:
            (is_ready, reason)
        """
        total_cases = len(self._cases)
        
        if total_cases < self._bootstrap_target:
            return False, f"only {total_cases} cases; need {self._bootstrap_target} for bootstrap"
        
        # Check 95% pass rate across all categories
        summary = self.summary_by_category()
        overall_passed = sum(s["passed"] for s in summary.values())
        overall_total = sum(s["total"] for s in summary.values())
        pass_rate = overall_passed / overall_total if overall_total > 0 else 0.0
        
        if pass_rate < self._promotion_threshold:
            return False, f"pass rate {pass_rate:.1%} < {self._promotion_threshold:.1%}"
        
        return True, "bootstrap gate passed"
    
    def production_readiness(self) -> tuple[bool, str]:
        """Check if production gate is met.
        
        Returns:
            (is_ready, reason)
        """
        total_cases = len(self._cases)
        
        if total_cases < self._production_target:
            return False, f"only {total_cases} cases; need {self._production_target} for production"
        
        # Check 95% pass rate
        summary = self.summary_by_category()
        
        # Check that each category has minimum coverage
        for cat_name, cat_summary in summary.items():
            if cat_summary["total"] < 10:
                return False, f"category {cat_name} has only {cat_summary['total']} cases"
        
        overall_passed = sum(s["passed"] for s in summary.values())
        overall_total = sum(s["total"] for s in summary.values())
        pass_rate = overall_passed / overall_total if overall_total > 0 else 0.0
        
        if pass_rate < self._promotion_threshold:
            return False, f"pass rate {pass_rate:.1%} < {self._promotion_threshold:.1%}"
        
        return True, "production gate passed"
    
    def regression_test(self, case_id: str, test_func) -> EvaluationResult:
        """Run a regression test for a specific case.
        
        Args:
            case_id: ID of benchmark case
            test_func: Function that takes case and returns EvaluationResult
            
        Returns:
            EvaluationResult
        """
        case = next((c for c in self._cases if c.case_id == case_id), None)
        if not case:
            raise ValueError(f"case {case_id} not found")
        
        result = test_func(case)
        self.record_result(case_id, result)
        return result
