"""Planner lifecycle utilities: validation, DAG checks, budgets and replay identity."""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Iterable, Mapping, Sequence

from .planner_models import Action, ResourceEnvelope, StopReason, TaskPlan


def canonical_json(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, default=str)


def plan_fingerprint(plan: TaskPlan) -> str:
    payload = asdict(plan)
    return hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()


def validate_dag(actions: Sequence[Action]) -> None:
    ids = {a.action_id for a in actions}
    if len(ids) != len(actions):
        raise ValueError("duplicate action_id")
    graph = {a.action_id: tuple(a.prerequisites) for a in actions}
    for action in actions:
        missing = [p for p in action.prerequisites if p not in ids]
        if missing:
            raise ValueError(f"missing prerequisites for {action.action_id}: {missing}")
    state: dict[str, int] = {}

    def visit(node: str) -> None:
        mark = state.get(node, 0)
        if mark == 1:
            raise ValueError("execution plan contains a dependency cycle")
        if mark == 2:
            return
        state[node] = 1
        for parent in graph[node]:
            visit(parent)
        state[node] = 2

    for action_id in ids:
        visit(action_id)


def topological_order(actions: Sequence[Action]) -> tuple[str, ...]:
    validate_dag(actions)
    remaining = {a.action_id: set(a.prerequisites) for a in actions}
    order: list[str] = []
    while remaining:
        ready = sorted(k for k, deps in remaining.items() if not deps)
        if not ready:
            raise ValueError("dependency cycle")
        order.extend(ready)
        for key in ready:
            del remaining[key]
        for deps in remaining.values():
            deps.difference_update(ready)
    return tuple(order)


@dataclass(frozen=True)
class BudgetLedger:
    reserved: ResourceEnvelope
    consumed: ResourceEnvelope

    @staticmethod
    def empty() -> "BudgetLedger":
        zero = ResourceEnvelope()
        return BudgetLedger(zero, zero)


def _add(a: ResourceEnvelope, b: ResourceEnvelope) -> ResourceEnvelope:
    values = {name: getattr(a, name) + getattr(b, name) for name in a.__dataclass_fields__}
    return ResourceEnvelope(**values)


def reserve(available: ResourceEnvelope, request: ResourceEnvelope) -> ResourceEnvelope:
    available.validate(); request.validate()
    fields = {}
    for name in available.__dataclass_fields__:
        if name == "recovery_reserve_ratio":
            fields[name] = available.recovery_reserve_ratio
            continue
        if getattr(request, name) > getattr(available, name):
            raise ValueError(f"insufficient resource: {name}")
        fields[name] = getattr(available, name) - getattr(request, name)
    return ResourceEnvelope(**fields)


def choose_stop(plan: TaskPlan, remaining_search_units: int, all_required_claims_satisfied: bool,
                contradiction_open: bool = False) -> StopReason | None:
    if all_required_claims_satisfied and not contradiction_open:
        return StopReason.QUALITY_FLOOR
    if remaining_search_units <= 0:
        return StopReason.BUDGET_EXHAUSTED
    return None


def explain_plan(plan: TaskPlan) -> str:
    fp = plan_fingerprint(plan)
    return (
        f"mode={plan.task_mode.value}; claims={len(plan.claims)}; queries={len(plan.queries)}; "
        f"methods={len(plan.methods)}; actions={len(plan.actions)}; fingerprint={fp}"
    )
