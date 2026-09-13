import pytest

from backend.evidence_selection import (
    ContextPacketBudget,
    EvidenceCandidate,
    build_context_packet,
    estimate_tokens,
    select_evidence,
)


def test_selection_prefers_higher_source_and_relevance_scores():
    selected = select_evidence(
        (
            EvidenceCandidate("secondary", "panel", "IPS", "https://secondary.example", source_rank=1, relevance_score=9),
            EvidenceCandidate("official", "panel", "IPS", "https://official.example", source_rank=5, relevance_score=5),
        ), max_items=1, max_tokens=10)
    assert selected[0].evidence_id == "official"


def test_selection_deduplicates_claim_text():
    selected = select_evidence(
        (EvidenceCandidate("a", "panel", "IPS", "https://a.example", source_rank=3), EvidenceCandidate("b", "panel", "  ips ", "https://b.example", source_rank=2)),
        max_items=5, max_tokens=20)
    assert len(selected) == 1


def test_selection_respects_token_budget():
    selected = select_evidence((EvidenceCandidate("a", "one", "abcdefgh", "https://a.example", estimated_tokens=2), EvidenceCandidate("b", "two", "ijklmnop", "https://b.example", estimated_tokens=2)), max_items=5, max_tokens=2)
    assert len(selected) == 1


def test_candidate_validation_covers_all_fail_closed_guards():
    invalid_candidates = (EvidenceCandidate("", "claim", "text", "https://example.com"), EvidenceCandidate("id", "", "text", "https://example.com"), EvidenceCandidate("id", "claim", "text", ""), EvidenceCandidate("id", "claim", "text", "https://example.com", source_rank=-1), EvidenceCandidate("id", "claim", "text", "https://example.com", relevance_score=-1), EvidenceCandidate("id", "claim", "text", "https://example.com", estimated_tokens=-1))
    for candidate in invalid_candidates:
        with pytest.raises(ValueError): candidate.validate()


def test_invalid_budgets_and_token_estimator_fail_closed():
    with pytest.raises(ValueError): select_evidence((), max_items=0, max_tokens=10)
    with pytest.raises(ValueError): select_evidence((), max_items=1, max_tokens=0)
    with pytest.raises(ValueError): estimate_tokens("abcdefgh", chars_per_token=1)
    assert estimate_tokens("") == 0
    assert estimate_tokens("abcdefgh") == 2


def test_selection_can_stop_on_item_limit_and_skip_overlong_candidate():
    selected = select_evidence((EvidenceCandidate("long", "long", "abcdefgh", "https://long.example", estimated_tokens=10), EvidenceCandidate("short", "short", "abcd", "https://short.example", estimated_tokens=1)), max_items=1, max_tokens=2)
    assert [candidate.evidence_id for candidate in selected] == ["short"]


def test_context_packet_preserves_reserves_dedupes_and_hashes_deterministically():
    candidates = (EvidenceCandidate("a", "price", "₹100", "https://official.example", source_rank=5, estimated_tokens=2), EvidenceCandidate("dup", "price", "  ₹100 ", "https://secondary.example", source_rank=1, estimated_tokens=2), EvidenceCandidate("b", "weight", "1.2 kg", "https://official.example", source_rank=4, estimated_tokens=2), EvidenceCandidate("c", "noise", "extra", "https://other.example", source_rank=1, estimated_tokens=4))
    budget = ContextPacketBudget(total_tokens=10, answer_reserve_tokens=2, verification_reserve_tokens=2)
    packet = build_context_packet(candidates, budget=budget, max_items=5)
    assert [item.evidence_id for item in packet.selected] == ["a", "b"]
    assert packet.evidence_tokens == 4
    assert "dup" in packet.dropped_ids
    assert "c" in packet.dropped_ids
    assert packet.duplicate_count >= 1
    assert 0 < packet.total_budget_used_ratio < 1
    assert packet.content_hash == build_context_packet(candidates, budget=budget, max_items=5).content_hash
    assert packet.prefix_cache_key == build_context_packet(candidates, budget=budget, max_items=5).prefix_cache_key


def test_context_packet_budget_guards_and_zero_candidate_packet():
    with pytest.raises(ValueError): ContextPacketBudget(10, 5, 5).validate()
    with pytest.raises(ValueError): ContextPacketBudget(0).validate()
    with pytest.raises(ValueError): ContextPacketBudget(10, -1, 0).validate()
    with pytest.raises(ValueError): build_context_packet((), budget=ContextPacketBudget(10), max_items=0)
    packet = build_context_packet((), budget=ContextPacketBudget(10, 2, 2), max_items=1)
    assert packet.selected == ()
    assert packet.evidence_tokens == 0
    assert packet.total_budget_used_ratio == 0


def test_context_packet_duplicate_order_and_dropped_accounting_branches():
    low_rank = EvidenceCandidate("low", "claim", "same", "https://low.example", source_rank=1, estimated_tokens=1)
    high_rank = EvidenceCandidate("high", "claim", "same", "https://high.example", source_rank=5, estimated_tokens=1)
    noise = EvidenceCandidate("noise", "noise", "different", "https://noise.example", source_rank=0, estimated_tokens=20)
    packet = build_context_packet((low_rank, noise, high_rank), budget=ContextPacketBudget(total_tokens=4, answer_reserve_tokens=1, verification_reserve_tokens=1), max_items=2)
    assert [item.evidence_id for item in packet.selected] == ["high"]
    assert "low" in packet.dropped_ids
    assert "noise" in packet.dropped_ids
