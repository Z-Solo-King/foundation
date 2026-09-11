import pytest

from backend.evidence_selection import EvidenceCandidate, estimate_tokens, select_evidence


def test_selection_prefers_higher_source_and_relevance_scores():
    selected = select_evidence(
        (
            EvidenceCandidate("secondary", "panel", "IPS", "https://secondary.example", source_rank=1, relevance_score=9),
            EvidenceCandidate("official", "panel", "IPS", "https://official.example", source_rank=5, relevance_score=5),
        ),
        max_items=1,
        max_tokens=10,
    )
    assert selected[0].evidence_id == "official"


def test_selection_deduplicates_claim_text():
    selected = select_evidence(
        (
            EvidenceCandidate("a", "panel", "IPS", "https://a.example", source_rank=3),
            EvidenceCandidate("b", "panel", "  ips ", "https://b.example", source_rank=2),
        ),
        max_items=5,
        max_tokens=20,
    )
    assert len(selected) == 1


def test_selection_respects_token_budget():
    selected = select_evidence(
        (
            EvidenceCandidate("a", "one", "abcdefgh", "https://a.example", estimated_tokens=2),
            EvidenceCandidate("b", "two", "ijklmnop", "https://b.example", estimated_tokens=2),
        ),
        max_items=5,
        max_tokens=2,
    )
    assert len(selected) == 1


def test_candidate_validation_covers_all_fail_closed_guards():
    invalid_candidates = (
        EvidenceCandidate("", "claim", "text", "https://example.com"),
        EvidenceCandidate("id", "", "text", "https://example.com"),
        EvidenceCandidate("id", "claim", "text", ""),
        EvidenceCandidate("id", "claim", "text", "https://example.com", source_rank=-1),
        EvidenceCandidate("id", "claim", "text", "https://example.com", relevance_score=-1),
        EvidenceCandidate("id", "claim", "text", "https://example.com", estimated_tokens=-1),
    )
    for candidate in invalid_candidates:
        with pytest.raises(ValueError):
            candidate.validate()


def test_invalid_budgets_and_token_estimator_fail_closed():
    with pytest.raises(ValueError):
        select_evidence((), max_items=0, max_tokens=10)
    with pytest.raises(ValueError):
        select_evidence((), max_items=1, max_tokens=0)
    with pytest.raises(ValueError):
        estimate_tokens("abcdefgh", chars_per_token=1)
    assert estimate_tokens("") == 0
    assert estimate_tokens("abcdefgh") == 2


def test_selection_can_stop_on_item_limit_and_skip_overlong_candidate():
    selected = select_evidence(
        (
            EvidenceCandidate("long", "long", "abcdefgh", "https://long.example", estimated_tokens=10),
            EvidenceCandidate("short", "short", "abcd", "https://short.example", estimated_tokens=1),
        ),
        max_items=1,
        max_tokens=2,
    )
    assert [candidate.evidence_id for candidate in selected] == ["short"]
