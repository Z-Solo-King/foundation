"""Provider router with capability-aware routing and free-eligibility gates.

Routes AI/extraction/acquisition tasks through provider-neutral interfaces.
Enforces free-tier eligibility, quota checks, and cost constraints before
any call to external providers.
"""

from dataclasses import dataclass
from typing import Callable, Any

from backend.execution.providers import ProviderRegistry, ProviderCapability
from backend.execution.resources import ResourceBudget, ResourceError


@dataclass(frozen=True)
class RoutingDecision:
    """Result of capability routing."""
    provider: str
    capability: str
    priority: int
    free_eligible: bool
    approved: bool
    reason: str = ""


class ProviderRouter:
    """Routes tasks to providers based on capability, cost, and availability."""
    
    def __init__(self, registry: ProviderRegistry, budget: ResourceBudget):
        self.registry = registry
        self.budget = budget
    
    def route(
        self,
        capability: str,
        strict_zero_cost_only: bool = True,
    ) -> RoutingDecision:
        """Route a capability request to a provider.
        
        Args:
            capability: The capability name (e.g., "search", "extraction")
            strict_zero_cost_only: If True, only free-eligible providers
            
        Returns:
            RoutingDecision with approval status and reason
        """
        best = self.registry.best(capability, free_only=strict_zero_cost_only)
        
        if not best:
            return RoutingDecision(
                provider="",
                capability=capability,
                priority=0,
                free_eligible=False,
                approved=False,
                reason=f"no {'free-eligible' if strict_zero_cost_only else ''} provider for {capability}",
            )
        
        # Check budget before approval
        if not best.enabled:
            return RoutingDecision(
                provider=best.provider,
                capability=best.capability,
                priority=best.priority,
                free_eligible=best.free_eligible,
                approved=False,
                reason=f"provider {best.provider} is disabled",
            )
        
        if strict_zero_cost_only and not best.free_eligible:
            return RoutingDecision(
                provider=best.provider,
                capability=best.capability,
                priority=best.priority,
                free_eligible=best.free_eligible,
                approved=False,
                reason=f"provider {best.provider} is not free-eligible; strict $0 cost enforced",
            )
        
        # Budget gate for inference calls
        if capability in ("extraction", "synthesis", "ranking"):
            try:
                # Don't actually consume yet; just check
                remaining = self.budget.remaining()
                if remaining["inference_calls"] <= 0:
                    return RoutingDecision(
                        provider=best.provider,
                        capability=best.capability,
                        priority=best.priority,
                        free_eligible=best.free_eligible,
                        approved=False,
                        reason="inference budget exhausted",
                    )
            except ResourceError as e:
                return RoutingDecision(
                    provider=best.provider,
                    capability=best.capability,
                    priority=best.priority,
                    free_eligible=best.free_eligible,
                    approved=False,
                    reason=str(e),
                )
        
        return RoutingDecision(
            provider=best.provider,
            capability=best.capability,
            priority=best.priority,
            free_eligible=best.free_eligible,
            approved=True,
            reason="approved",
        )
    
    def execute(
        self,
        capability: str,
        func: Callable,
        *args,
        strict_zero_cost_only: bool = True,
        consume_inference: bool = True,
        **kwargs,
    ) -> Any:
        """Route and execute a capability.
        
        Args:
            capability: The capability to route
            func: The function to execute if approved
            args: Positional arguments for func
            strict_zero_cost_only: Enforce $0 cost constraint
            consume_inference: If True, consume inference quota
            kwargs: Keyword arguments for func
            
        Returns:
            Result of func if approved, raises otherwise
        """
        decision = self.route(capability, strict_zero_cost_only)
        
        if not decision.approved:
            raise PermissionError(f"Routing denied: {decision.reason}")
        
        if consume_inference:
            self.budget.consume_inference()
        
        return func(*args, **kwargs)
