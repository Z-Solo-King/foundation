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


def test_invalid_budgets_and_candidate_scores_fail_closed():
    with pytest.raises(ValueError):
        select_evidence((), max_items=0, max_tokens=10)
    with pytest.raises(ValueError):
        EvidenceCandidate("", "claim", "text", "https://example.com").validate()
    assert estimate_tokens("abcdefgh") == 2
