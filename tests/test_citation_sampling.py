from datetime import datetime, timedelta, timezone

import pytest

from backend.citation_sampling import (
    MAX_CITATIONS_PER_OUTPUT,
    ReviewOutcome,
    CitationPrecisionMetric,
    CitationRef,
    CitationReview,
    ResearchOutputSample,
    build_precision_metric,
    metric_now,
    select_citation_samples,
)


BASE = datetime(2026, 9, 18, 10, 0, tzinfo=timezone.utc)


def citation(cid="c1", claim="claim", url="https://example.com", obs="obs-1"):
    return CitationRef(cid, claim, url, obs, "support text")


def output(oid="o1", at=BASE, citations=(citation(),), **changes):
    values = dict(output_id=oid, generated_at=at, citations=citations, execution_digest="digest")
    values.update(changes)
    return ResearchOutputSample(**values)


def review(cid="c1", oid="o1", outcome=ReviewOutcome.SUPPORTED, at=BASE, reviewer="reviewer"):
    return CitationReview(cid, oid, at, outcome, reviewer)


def test_sampling_is_deterministic_and_prefers_recent_outputs():
    newer = output("o-new", BASE + timedelta(minutes=1), (citation("c2"),))
    older = output("o-old", BASE, (citation("c1"),))
    first = select_citation_samples((older, newer), max_outputs=2, max_citations=2)
    second = select_citation_samples((newer, older), max_outputs=2, max_citations=2)
    assert first == second
    assert {item.output_id for item in first} == {"o-old", "o-new"}


def test_sampling_respects_window_and_caps():
    outputs = tuple(
        output(str(i), BASE + timedelta(minutes=i), tuple(citation(f"c{i}-{j}") for j in range(3)))
        for i in range(6)
    )
    samples = select_citation_samples(
        outputs,
        max_outputs=3,
        max_citations=4,
        window_start=BASE + timedelta(minutes=2),
        window_end=BASE + timedelta(minutes=5),
    )
    assert len(samples) == 4


def test_sampling_validation_is_fail_closed():
    with pytest.raises(ValueError, match="max_outputs"):
        select_citation_samples((output(),), max_outputs=0, max_citations=1)
    with pytest.raises(ValueError, match="max_citations"):
        select_citation_samples((output(),), max_outputs=1, max_citations=0)
    with pytest.raises(ValueError, match="window_start"):
        select_citation_samples((output(),), max_outputs=1, max_citations=1, window_start=datetime(2026, 9, 18))
    with pytest.raises(ValueError, match="window_end"):
        select_citation_samples((output(),), max_outputs=1, max_citations=1, window_end=datetime(2026, 9, 18))
    with pytest.raises(ValueError, match="precede"):
        select_citation_samples((output(),), max_outputs=1, max_citations=1, window_start=BASE + timedelta(days=1), window_end=BASE)
    with pytest.raises(ValueError, match="output count"):
        select_citation_samples(tuple(output(str(i)) for i in range(10_001)), max_outputs=1, max_citations=1)


def test_output_and_citation_validation():
    with pytest.raises(ValueError, match="output_id"):
        output("").validate()
    with pytest.raises(ValueError, match="timezone"):
        output(at=datetime(2026, 9, 18)).validate()
    with pytest.raises(ValueError, match="citation count"):
        output(citations=tuple(citation(str(i)) for i in range(MAX_CITATIONS_PER_OUTPUT + 1))).validate()
    with pytest.raises(ValueError, match="citation_id"):
        citation("").validate()
    with pytest.raises(ValueError, match="claim"):
        citation(claim="").validate()
    with pytest.raises(ValueError, match="source_url"):
        citation(url="").validate()
    with pytest.raises(ValueError, match="observation_id"):
        citation(obs="").validate()
    with pytest.raises(ValueError, match="unique"):
        output(citations=(citation(), citation())).validate()


def test_metric_ignores_out_of_window_and_unrelated_reviews():
    samples = (select_citation_samples((output(),), max_outputs=1, max_citations=1)[0],)
    reviews = (
        review(outcome=ReviewOutcome.SUPPORTED),
        review(oid="other", outcome=ReviewOutcome.UNSUPPORTED),
        review(at=BASE - timedelta(days=1), outcome=ReviewOutcome.UNSUPPORTED),
    )
    metric = build_precision_metric(
        samples,
        reviews,
        window_start=BASE,
        window_end=BASE + timedelta(days=1),
    )
    assert metric.supported == 1
    assert metric.unsupported == 0
    assert metric.unresolved == 0
    assert metric.precision == 1.0


def test_metric_counts_unresolved_and_unresolved_only_precision_is_none():
    sample = CitationRef("c2", "claim", "https://example.com", "obs-2")
    samples = select_citation_samples((output("o2", citations=(sample,)),), max_outputs=1, max_citations=1)
    metric = build_precision_metric(samples, (), window_start=BASE, window_end=BASE + timedelta(days=1))
    assert metric.unresolved == 1
    assert metric.precision is None


def test_metric_rejects_duplicate_sample_or_review_and_bad_windows():
    sample = select_citation_samples((output(),), max_outputs=1, max_citations=1)[0]
    with pytest.raises(ValueError, match="duplicate citation"):
        build_precision_metric((sample, sample), (), window_start=BASE, window_end=BASE)
    with pytest.raises(ValueError, match="multiple reviews"):
        build_precision_metric(
            (sample,),
            (review(), review(at=BASE + timedelta(minutes=1))),
            window_start=BASE,
            window_end=BASE + timedelta(days=1),
        )
    with pytest.raises(ValueError, match="window_end"):
        build_precision_metric((sample,), (), window_start=BASE, window_end=datetime(2026, 9, 18))
    with pytest.raises(ValueError, match="window_start"):
        build_precision_metric((sample,), (), window_start=datetime(2026, 9, 18), window_end=BASE)
    with pytest.raises(ValueError, match="sample count"):
        build_precision_metric(
            tuple(
                __import__("backend.citation_sampling", fromlist=["CitationSample"]).CitationSample(str(i), str(i), i)
                for i in range(1_025)
            ),
            (),
            window_start=BASE,
            window_end=BASE,
        )


def test_review_validation_and_metric_invariants():
    with pytest.raises(ValueError, match="identity"):
        CitationReview("", "o1", BASE, ReviewOutcome.SUPPORTED, "reviewer").validate()
    with pytest.raises(ValueError, match="reviewer_id"):
        CitationReview("c1", "o1", BASE, ReviewOutcome.SUPPORTED, "").validate()
    with pytest.raises(ValueError, match="timezone"):
        CitationReview("c1", "o1", datetime(2026, 9, 18), ReviewOutcome.SUPPORTED, "r").validate()
    with pytest.raises(ValueError, match="SHA-256"):
        CitationReview("c1", "o1", BASE, ReviewOutcome.SUPPORTED, "r", "bad").validate()
    with pytest.raises(ValueError, match="precision counts"):
        CitationPrecisionMetric(BASE, BASE, 1, 1, 1, -1).validate()
    with pytest.raises(ValueError, match="sum"):
        CitationPrecisionMetric(BASE, BASE, 2, 1, 0, 0).validate()
    with pytest.raises(ValueError, match="window_end"):
        CitationPrecisionMetric(BASE + timedelta(days=1), BASE, 0, 0, 0, 0).validate()


def test_metric_to_dict_and_now_are_bounded():
    metric = CitationPrecisionMetric(BASE, BASE, 1, 1, 0, 0)
    payload = metric.to_dict()
    assert payload["schema"] == "citation-precision-sampling/v1"
    assert payload["precision"] == 1.0
    now = metric_now()
    assert now.tzinfo is not None
