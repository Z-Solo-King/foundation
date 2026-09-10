"""Tests for provider routing."""

import pytest
from backend.execution.router import ProviderRouter, RoutingDecision
from backend.execution.providers import ProviderRegistry, ProviderCapability
from backend.execution.resources import ResourceBudget


def test_router_no_provider():
    """Router returns unapproved decision when no provider available."""
    registry = ProviderRegistry()
    budget = ResourceBudget()
    router = ProviderRouter(registry, budget)
    
    decision = router.route("unknown_capability")
    assert decision.approved is False
    assert "no" in decision.reason.lower()


def test_router_free_eligible():
    """Router approves free-eligible provider."""
    registry = ProviderRegistry()
    registry.register(ProviderCapability("free-provider", "search", free_eligible=True, priority=10))
    
    budget = ResourceBudget()
    router = ProviderRouter(registry, budget)
    
    decision = router.route("search", strict_zero_cost_only=True)
    assert decision.approved is True
    assert decision.provider == "free-provider"


def test_router_rejects_paid_with_strict_zero():
    """Router rejects paid provider when strict $0 cost enforced."""
    registry = ProviderRegistry()
    registry.register(ProviderCapability("paid-provider", "search", free_eligible=False, priority=1))
    registry.register(ProviderCapability("free-provider", "search", free_eligible=True, priority=20))
    
    budget = ResourceBudget()
    router = ProviderRouter(registry, budget)
    
    decision = router.route("search", strict_zero_cost_only=True)
    assert decision.approved is True
    assert decision.provider == "free-provider"  # Should pick the free one


def test_router_inference_budget_exhausted():
    """Router rejects inference capability when budget exhausted."""
    registry = ProviderRegistry()
    registry.register(ProviderCapability("ai-provider", "extraction", free_eligible=True))
    
    budget = ResourceBudget(inference_calls=0)  # No inference budget
    router = ProviderRouter(registry, budget)
    
    decision = router.route("extraction", strict_zero_cost_only=True)
    assert decision.approved is False
    assert "budget" in decision.reason.lower()


def test_router_disabled_provider():
    """Router rejects disabled provider."""
    registry = ProviderRegistry()
    registry.register(ProviderCapability("provider", "search", enabled=False))
    
    budget = ResourceBudget()
    router = ProviderRouter(registry, budget)
    
    decision = router.route("search", strict_zero_cost_only=True)
    assert decision.approved is False
    assert "disabled" in decision.reason.lower()
