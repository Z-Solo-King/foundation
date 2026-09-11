"""Evaluation harness for regression testing and benchmark promotion.

Bootstrap benchmark: 50 representative cases.
Production gate: 150-300 cases before promotion.
Continuous adversarial testing.
"""

from dataclasses import dataclass
from enum import StrEnum
from typing import Any, Callable


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
    adversarial_aspect: str | None = None
    difficulty: str = "normal"


@dataclass(frozen=True)
class EvaluationResult:
    """Result of evaluating a single case."""
    case_id: str
    passed: bool
    metric_value: float | None = None
    error: str | None = None
    latency_ms: float | None = None
    notes: str = ""


class EvaluationHarness:
    """Runs benchmark suite and tracks promotion readiness."""

    def __init__(self):
        self._cases: list[BenchmarkCase] = []
        self._case_index: dict[str, BenchmarkCase] = {}
        self._results: dict[str, list[EvaluationResult]] = {}
        self._promotion_threshold = 0.95
        self._bootstrap_target = 50
        self._production_target = 150

    def register_case(self, case: BenchmarkCase) -> None:
        """Register a benchmark case in O(1) duplicate-check time."""
        if case.case_id in self._case_index:
            raise ValueError(f"case {case.case_id} already registered")
        self._cases.append(case)
        self._case_index[case.case_id] = case

    def record_result(self, case_id: str, result: EvaluationResult) -> None:
        """Record evaluation result for a case."""
        if case_id not in self._case_index:
            raise ValueError(f"case {case_id} not registered")
        self._results.setdefault(case_id, []).append(result)

    def summary_by_category(self) -> dict[str, dict[str, Any]]:
        """Get summary statistics by category."""
        by_cat = {cat: {"passed": 0, "total": 0} for cat in EvaluationCategory}
        for case in self._cases:
            counts = by_cat[case.category]
            counts["total"] += 1
            results = self._results.get(case.case_id)
            if results and results[-1].passed:
                counts["passed"] += 1

        return {
            str(category): {
                "passed": counts["passed"],
                "total": counts["total"],
                "pass_rate": counts["passed"] / counts["total"] if counts["total"] else 0.0,
            }
            for category, counts in by_cat.items()
        }

    def bootstrap_readiness(self) -> tuple[bool, str]:
        """Check if bootstrap benchmark gate is met."""
        total_cases = len(self._cases)
        if total_cases < self._bootstrap_target:
            return False, f"only {total_cases} cases; need {self._bootstrap_target} for bootstrap"
        summary = self.summary_by_category()
        overall_passed = sum(s["passed"] for s in summary.values())
        overall_total = sum(s["total"] for s in summary.values())
        pass_rate = overall_passed / overall_total if overall_total else 0.0
        if pass_rate < self._promotion_threshold:
            return False, f"pass rate {pass_rate:.1%} < {self._promotion_threshold:.1%}"
        return True, "bootstrap gate passed"

    def production_readiness(self) -> tuple[bool, str]:
        """Check if production gate is met."""
        total_cases = len(self._cases)
        if total_cases < self._production_target:
            return False, f"only {total_cases} cases; need {self._production_target} for production"
        summary = self.summary_by_category()
        for cat_name, cat_summary in summary.items():
            if cat_summary["total"] < 10:
                return False, f"category {cat_name} has only {cat_summary['total']} cases"
        overall_passed = sum(s["passed"] for s in summary.values())
        overall_total = sum(s["total"] for s in summary.values())
        pass_rate = overall_passed / overall_total if overall_total else 0.0
        if pass_rate < self._promotion_threshold:
            return False, f"pass rate {pass_rate:.1%} < {self._promotion_threshold:.1%}"
        return True, "production gate passed"

    def regression_test(self, case_id: str, test_func: Callable[[BenchmarkCase], EvaluationResult]) -> EvaluationResult:
        """Run and record a regression test for a specific case."""
        case = self._case_index.get(case_id)
        if case is None:
            raise ValueError(f"case {case_id} not found")
        result = test_func(case)
        self.record_result(case_id, result)
        return result
