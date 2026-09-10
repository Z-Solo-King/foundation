"""Deterministic public-safe bootstrap benchmark: exactly 50 cases."""

from backend.evaluation.harness import BenchmarkCase, EvaluationCategory


def _case(category, index, description, expected_output, adversarial=None, difficulty="normal"):
    return BenchmarkCase(
        case_id=f"{category.value}-{index}",
        category=category,
        description=description,
        input_question=f"Bootstrap {category.value} case {index}",
        expected_output=expected_output,
        adversarial_aspect=adversarial,
        difficulty=difficulty,
    )


def create_bootstrap_corpus() -> list[BenchmarkCase]:
    """Create 50 public-safe benchmark cases, 5 per category."""
    corpus = []
    for category in EvaluationCategory:
        for index in range(1, 6):
            if category == EvaluationCategory.RETRIEVAL:
                expected, desc, adv = {"status": "retrievable"}, "deterministic retrieval behavior", None
            elif category == EvaluationCategory.EXTRACTION:
                expected, desc, adv = {"status": "extractable"}, "structured extraction behavior", None
            elif category == EvaluationCategory.CONTRADICTION:
                expected, desc, adv = {"status": "conflict-aware"}, "contradiction handling", "conflicting sources" if index == 5 else None
            elif category == EvaluationCategory.TEMPORAL:
                expected, desc, adv = {"status": "time-aware"}, "temporal validity handling", "stale evidence" if index == 5 else None
            elif category == EvaluationCategory.INDEPENDENCE:
                expected, desc, adv = {"status": "lineage-aware"}, "source-family independence handling", "republished content" if index == 5 else None
            elif category == EvaluationCategory.CITATION:
                expected, desc, adv = {"status": "traceable"}, "citation-chain preservation", "broken citation" if index == 5 else None
            elif category == EvaluationCategory.FRESHNESS:
                expected, desc, adv = {"status": "freshness-checked"}, "freshness handling", "stale data" if index == 5 else None
            elif category == EvaluationCategory.RESOURCE:
                expected, desc, adv = {"status": "budget-enforced"}, "hard resource envelope", "budget exhaustion" if index == 5 else None
            elif category == EvaluationCategory.SECURITY:
                expected, desc, adv = {"status": "blocked-or-safe"}, "security boundary handling", "SSRF" if index == 5 else None
            else:
                expected, desc, adv = {"status": "single-owner"}, "architecture conformance", "duplicate owner" if index == 5 else None
            corpus.append(_case(category, index, desc, expected, adv, "hard" if index >= 4 else "normal"))
    assert len(corpus) == 50
    return corpus
