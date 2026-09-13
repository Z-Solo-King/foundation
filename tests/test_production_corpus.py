from backend.evaluation.harness import EvaluationCategory
from backend.evaluation.production_corpus import create_production_corpus


def test_production_corpus_has_150_unique_cases_and_full_category_coverage():
    corpus = create_production_corpus()
    assert len(corpus) == 150
    assert len({case.case_id for case in corpus}) == 150
    counts = {category: 0 for category in EvaluationCategory}
    for case in corpus:
        counts[case.category] += 1
    assert all(count == 15 for count in counts.values())


def test_production_corpus_has_adversarial_and_recovery_variants():
    corpus = create_production_corpus()
    aspects = {case.adversarial_aspect for case in corpus if case.adversarial_aspect}
    assert "adversarial perturbation" in aspects
    assert "recovery-path decision" in aspects
    assert "conflicting or misleading input" in aspects
