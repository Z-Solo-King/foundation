"""Deterministic public-safe production benchmark corpus.

The corpus deliberately uses structural case families rather than external data so it is
stable, reproducible and safe to run in CI. Real-source golden cases can be layered on later.
"""

from backend.evaluation.harness import BenchmarkCase, EvaluationCategory


_VARIANTS = (
    ("base", "normal", None),
    ("boundary", "hard", "boundary condition"),
    ("adversarial", "hard", "adversarial perturbation"),
    ("poisoned", "hard", "conflicting or misleading input"),
    ("stale", "hard", "stale or expired information"),
    ("partial", "hard", "partial evidence or incomplete payload"),
    ("duplicate", "hard", "duplicate or republished evidence"),
    ("policy", "hard", "policy or access boundary"),
    ("quota", "hard", "resource or quota pressure"),
    ("format", "normal", "representation-format variation"),
    ("multilingual", "normal", "language variation"),
    ("replay", "hard", "replay/context drift"),
    ("lineage", "hard", "source-lineage ambiguity"),
    ("precision", "hard", "precision or normalization edge"),
    ("recovery", "hard", "recovery-path decision"),
)

_EXPECTATIONS = {
    EvaluationCategory.RETRIEVAL: ("retrievable", "retrieval selection and bounded source escalation"),
    EvaluationCategory.EXTRACTION: ("extractable", "deterministic extraction without invented fields"),
    EvaluationCategory.CONTRADICTION: ("conflict-aware", "contradiction detection and fail-closed adjudication"),
    EvaluationCategory.TEMPORAL: ("time-aware", "temporal validity and historical/current distinction"),
    EvaluationCategory.INDEPENDENCE: ("lineage-aware", "independent-origin and republisher handling"),
    EvaluationCategory.CITATION: ("traceable", "citation entailment and reconstructable provenance"),
    EvaluationCategory.FRESHNESS: ("freshness-checked", "freshness thresholds and stale evidence"),
    EvaluationCategory.RESOURCE: ("budget-enforced", "hard resource and recovery-reserve enforcement"),
    EvaluationCategory.SECURITY: ("blocked-or-safe", "security and untrusted-input boundaries"),
    EvaluationCategory.ARCHITECTURE: ("single-owner", "single canonical owner and protected boundary"),
}


def create_production_corpus() -> list[BenchmarkCase]:
    corpus: list[BenchmarkCase] = []
    for category in EvaluationCategory:
        expected, description = _EXPECTATIONS[category]
        for index, (variant, difficulty, adversarial) in enumerate(_VARIANTS, start=1):
            case_number = index
            corpus.append(
                BenchmarkCase(
                    case_id=f"production-{category.value}-{case_number:02d}",
                    category=category,
                    description=f"{description}; {variant} variant",
                    input_question=f"Production {category.value} evaluation {case_number:02d}: {variant}",
                    expected_output={"status": expected, "variant": variant},
                    adversarial_aspect=adversarial,
                    difficulty=difficulty,
                )
            )
    assert len(corpus) == 150
    assert len({case.case_id for case in corpus}) == 150
    return corpus


__all__ = ["create_production_corpus"]