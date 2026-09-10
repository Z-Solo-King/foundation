"""Tests for promotion gate."""

import pytest
from backend.learning.promotion import (
    PromotionGate,
    BehaviorChange,
    EvaluationMetrics,
    PromotionMode,
)


def dummy_old(x):
    return x * 2


def dummy_new(x):
    return x * 2.1  # Slight improvement


def test_register_change():
    """Changes can be registered."""
    gate = PromotionGate()
    change = BehaviorChange(
        change_id="ch-1",
        description="Improve extraction",
        affected_component="extractor",
        old_implementation=dummy_old,
        new_implementation=dummy_new,
    )
    gate.register_change(change)
    assert "ch-1" in gate._changes


def test_protected_policy_cannot_change():
    """Protected policy changes are rejected."""
    gate = PromotionGate()
    change = BehaviorChange(
        change_id="ch-1",
        description="Weaken privacy",
        affected_component="privacy_gate",
        old_implementation=lambda x: x,
        new_implementation=lambda x: x,
        is_mutable=False,  # Protected
    )
    
    with pytest.raises(ValueError, match="protected policy"):
        gate.register_change(change)


def test_shadow_evaluation():
    """Shadow mode evaluates old vs new."""
    gate = PromotionGate()
    change = BehaviorChange(
        change_id="ch-1",
        description="Test",
        affected_component="test",
        old_implementation=dummy_old,
        new_implementation=dummy_new,
    )
    gate.register_change(change)
    
    test_cases = [1, 2, 3, 4, 5]
    
    def evaluator(old_result, new_result, case):
        # Score: closeness to case * 10
        old_score = 100 if old_result else 0
        new_score = 100 if new_result else 0
        return old_score, new_score
    
    metrics = gate.shadow_evaluation("ch-1", test_cases, evaluator)
    assert metrics.old_score > 0
    assert metrics.new_score > 0


def test_approve_canary():
    """Canary approval checks regression threshold."""
    gate = PromotionGate()
    change = BehaviorChange(
        change_id="ch-1",
        description="Test",
        affected_component="test",
        old_implementation=dummy_old,
        new_implementation=dummy_new,
    )
    gate.register_change(change)
    
    # Good metrics: improvement, low regression
    metrics = EvaluationMetrics(
        old_score=90.0,
        new_score=92.0,
        improvement=2.0,
        latency_old_ms=100.0,
        latency_new_ms=95.0,
        regression_count=1,  # 1 out of 100
        improvement_count=10,
        neutral_count=89,
    )
    
    approved, reason = gate.approve_canary("ch-1", metrics)
    assert approved is True
    assert gate._modes["ch-1"] == PromotionMode.CANARY


def test_reject_canary_on_regression():
    """Canary rejected if regression too high."""
    gate = PromotionGate()
    change = BehaviorChange(
        change_id="ch-1",
        description="Test",
        affected_component="test",
        old_implementation=dummy_old,
        new_implementation=dummy_new,
    )
    gate.register_change(change)
    
    # Bad metrics: high regression
    metrics = EvaluationMetrics(
        old_score=90.0,
        new_score=85.0,
        improvement=-5.0,
        latency_old_ms=100.0,
        latency_new_ms=105.0,
        regression_count=10,  # Too many
        improvement_count=2,
        neutral_count=88,
    )
    
    approved, reason = gate.approve_canary("ch-1", metrics)
    assert approved is False
    assert "regression" in reason.lower()


def test_promotion_to_production():
    """Approve promotion to production."""
    gate = PromotionGate()
    change = BehaviorChange(
        change_id="ch-1",
        description="Test",
        affected_component="test",
        old_implementation=dummy_old,
        new_implementation=dummy_new,
    )
    gate.register_change(change)
    
    # Approve canary first
    metrics = EvaluationMetrics(
        old_score=90.0,
        new_score=91.5,
        improvement=1.5,
        latency_old_ms=100.0,
        latency_new_ms=98.0,
        regression_count=1,
        improvement_count=15,
        neutral_count=84,
    )
    gate.approve_canary("ch-1", metrics)
    
    # Promote to production
    approved, reason = gate.approve_promotion("ch-1", metrics)
    assert approved is True
    assert gate._modes["ch-1"] == PromotionMode.PROMOTED


def test_automatic_rollback():
    """Automatic rollback on production regression."""
    gate = PromotionGate()
    change = BehaviorChange(
        change_id="ch-1",
        description="Test",
        affected_component="test",
        old_implementation=dummy_old,
        new_implementation=dummy_new,
    )
    gate.register_change(change)
    gate._modes["ch-1"] = PromotionMode.PROMOTED
    
    # Production metrics: high regression
    metrics = EvaluationMetrics(
        old_score=90.0,
        new_score=80.0,
        improvement=-10.0,
        latency_old_ms=100.0,
        latency_new_ms=110.0,
        regression_count=15,  # 15% regression
        improvement_count=2,
        neutral_count=83,
    )
    
    should_rollback, reason = gate.check_rollback("ch-1", metrics)
    assert should_rollback is True
    assert gate._modes["ch-1"] == PromotionMode.ROLLED_BACK
