import pytest

from backend.intelligence.strategy_contracts import (
    CacheProfile,
    RetryPolicy,
    StrategyCard,
    StrategyFamily,
    TokenBudget,
    TokenDecisionKind,
    choose_token_decision,
)


def test_retry_policy_delay_and_validation():
    policy = RetryPolicy(max_attempts=3, base_delay_seconds=2, max_delay_seconds=5, multiplier=2, jitter_ratio=0.2)
    assert policy.delay_seconds(1) == 2
    assert policy.delay_seconds(2) == 4
    assert policy.delay_seconds(3) == 5
    with pytest.raises(ValueError): RetryPolicy(max_attempts=0).validate()
    with pytest.raises(ValueError): RetryPolicy(base_delay_seconds=-1).validate()
    with pytest.raises(ValueError): RetryPolicy(base_delay_seconds=4, max_delay_seconds=3).validate()
    with pytest.raises(ValueError): RetryPolicy(multiplier=.5).validate()
    with pytest.raises(ValueError): RetryPolicy(jitter_ratio=1.1).validate()
    with pytest.raises(ValueError): policy.delay_seconds(0)


def test_cache_and_token_budget_validation():
    CacheProfile(freshness_seconds=0).validate()
    with pytest.raises(ValueError): CacheProfile(freshness_seconds=-1).validate()
    budget = TokenBudget(100, 50, 200, verification_reserve=20, final_answer_reserve=10)
    assert budget.usable_limit == 170
    with pytest.raises(ValueError): TokenBudget(-1, 1, 2).validate()
    with pytest.raises(ValueError): TokenBudget(100, 50, 100).validate()
    with pytest.raises(ValueError): TokenBudget(10, 10, 30, verification_reserve=20, final_answer_reserve=20).validate()


def test_strategy_card_validation_and_utility():
    card = StrategyCard(
        "api-v1", StrategyFamily.ACQUISITION, "foundation", expected_quality=.9,
        expected_completeness=.8, expected_latency_ms=100, expected_resource_units=.5,
        evidence_directness=.9, risk_penalty=.1, token_multiplier=1.2,
        cache=CacheProfile(exact=True, prefix_reusable=True), retry=RetryPolicy(),
    )
    card.validate()
    assert card.utility() > 0
    neutral = StrategyCard("html-v1", StrategyFamily.PARSER, "foundation", cache=CacheProfile(exact=False, prefix_reusable=False))
    assert neutral.utility() > 0
    base = {"strategy_id": "x", "family": StrategyFamily.QUERY, "owner": "o"}
    for changes in (
        {"strategy_id": " "},
        {"owner": " "},
        {"expected_quality": 1.1},
        {"expected_completeness": -0.1},
        {"evidence_directness": 1.1},
        {"expected_latency_ms": -1},
        {"expected_resource_units": -1},
        {"risk_penalty": -1},
        {"token_multiplier": 0},
    ):
        with pytest.raises(ValueError):
            StrategyCard(**{**base, **changes}).validate()


def test_token_decision_matrix():
    budget = TokenBudget(100, 50, 200, verification_reserve=20, final_answer_reserve=10)
    assert choose_token_decision(budget, 10, 10, exact_cache_hit=True).kind == TokenDecisionKind.CACHE
    assert choose_token_decision(budget, 50, 20).kind == TokenDecisionKind.ALLOW
    assert choose_token_decision(budget, 150, 10, prefix_cache_hit=True).kind == TokenDecisionKind.CACHE
    assert choose_token_decision(budget, 160, 50, compression_available=True).kind == TokenDecisionKind.COMPRESS
    assert choose_token_decision(budget, 160, 50, downgrade_available=True).kind == TokenDecisionKind.DOWNGRADE
    assert choose_token_decision(budget, 160, 50).kind == TokenDecisionKind.STOP
    with pytest.raises(ValueError): choose_token_decision(budget, -1, 1)
