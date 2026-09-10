"""Provider router with strict zero-cost and budget gates."""

from dataclasses import dataclass
from typing import Callable, Any
from backend.execution.providers import ProviderRegistry
from backend.execution.resources import ResourceBudget, ResourceError


@dataclass(frozen=True)
class RoutingDecision:
    provider: str
    capability: str
    priority: int
    free_eligible: bool
    approved: bool
    reason: str = ""


class ProviderRouter:
    def __init__(self, registry: ProviderRegistry, budget: ResourceBudget):
        self.registry = registry
        self.budget = budget

    def route(self, capability: str, strict_zero_cost_only: bool = True) -> RoutingDecision:
        # Surface an explicit disabled reason when a matching provider exists but is disabled.
        configured = [p for p in self.registry.snapshot() if p.capability == capability]
        if configured and not any(p.enabled for p in configured):
            best_disabled = sorted(configured, key=lambda p: p.priority)[0]
            return RoutingDecision(best_disabled.provider, capability, best_disabled.priority,
                                   best_disabled.free_eligible, False,
                                   f"provider {best_disabled.provider} is disabled")

        best = self.registry.best(capability, free_only=strict_zero_cost_only)
        if not best:
            return RoutingDecision("", capability, 0, False, False,
                                   f"no {'free-eligible ' if strict_zero_cost_only else ''}provider for {capability}")

        if strict_zero_cost_only and not best.free_eligible:
            return RoutingDecision(best.provider, best.capability, best.priority, False, False,
                                   f"provider {best.provider} is not free-eligible; strict $0 cost enforced")

        if capability in ("extraction", "synthesis", "ranking"):
            try:
                if self.budget.remaining()["inference_calls"] <= 0:
                    return RoutingDecision(best.provider, best.capability, best.priority,
                                           best.free_eligible, False,
                                           "inference budget exhausted")
            except (ResourceError, KeyError) as exc:
                return RoutingDecision(best.provider, best.capability, best.priority,
                                       best.free_eligible, False, str(exc))

        return RoutingDecision(best.provider, best.capability, best.priority,
                               best.free_eligible, True, "approved")

    def execute(self, capability: str, func: Callable, *args,
                strict_zero_cost_only: bool = True, consume_inference: bool = True,
                **kwargs) -> Any:
        decision = self.route(capability, strict_zero_cost_only)
        if not decision.approved:
            raise PermissionError(f"Routing denied: {decision.reason}")
        if consume_inference:
            self.budget.consume_inference()
        return func(*args, **kwargs)
