"""Adaptive replanning primitives.

This module decides when a plan is stale and what class of recovery is needed.
It never performs acquisition or mutates protected policy.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Mapping, Sequence

from .planner_models import Coverage, CoverageState, FailureClass, MethodCandidate, TaskPlan


class ReplanTrigger(str, Enum):
    LOW_YIELD = "low_yield"
    GAP = "gap"
    CONTRADICTION = "contradiction"
    SOURCE_DEGRADED = "source_degraded"
    CAPABILITY_CHANGED = "capability_changed"
    QUOTA_CHANGED = "quota_changed"
    POLICY_CHANGED = "policy_changed"
    FRESHNESS_EXPIRED = "freshness_expired"
    TEMPORAL_MISMATCH = "temporal_mismatch"
    METHOD_FAILED = "method_failed"


@dataclass(frozen=True)
class PlanContextFingerprint:
    capability_version: str
    policy_version: str
    source_profile_version: str
    quota_version: str
    freshness_epoch: str


@dataclass(frozen=True)
class ReplanDecision:
    required: bool
    triggers: tuple[ReplanTrigger, ...]
    reason_codes: tuple[str, ...] = ()
    preferred_actions: tuple[str, ...] = ()


def needs_replan(plan_context: PlanContextFingerprint, current: PlanContextFingerprint,
                 coverages: Sequence[Coverage] = (),
                 failures: Sequence[FailureClass] = ()) -> ReplanDecision:
    triggers: list[ReplanTrigger] = []
    reasons: list[str] = []
    if plan_context.capability_version != current.capability_version:
        triggers.append(ReplanTrigger.CAPABILITY_CHANGED); reasons.append("capability_version_changed")
    if plan_context.policy_version != current.policy_version:
        triggers.append(ReplanTrigger.POLICY_CHANGED); reasons.append("policy_version_changed")
    if plan_context.source_profile_version != current.source_profile_version:
        triggers.append(ReplanTrigger.SOURCE_DEGRADED); reasons.append("source_profile_changed")
    if plan_context.quota_version != current.quota_version:
        triggers.append(ReplanTrigger.QUOTA_CHANGED); reasons.append("quota_state_changed")
    if plan_context.freshness_epoch != current.freshness_epoch:
        triggers.append(ReplanTrigger.FRESHNESS_EXPIRED); reasons.append("freshness_epoch_changed")
    states = {c.state for c in coverages}
    if CoverageState.CONTRADICTED in states:
        triggers.append(ReplanTrigger.CONTRADICTION); reasons.append("claim_contradicted")
    if CoverageState.PARTIAL in states or CoverageState.UNSUPPORTED in states:
        triggers.append(ReplanTrigger.GAP); reasons.append("claim_gap")
    if CoverageState.STALE in states:
        triggers.append(ReplanTrigger.FRESHNESS_EXPIRED); reasons.append("stale_evidence")
    for failure in failures:
        if failure in {FailureClass.RATE_LIMITED, FailureClass.FORBIDDEN, FailureClass.CAPTCHA, FailureClass.AUTH_REQUIRED}:
            triggers.append(ReplanTrigger.METHOD_FAILED); reasons.append(f"method_failure:{failure.value}")
        elif failure in {FailureClass.PARSER, FailureClass.MALFORMED, FailureClass.ENCODING, FailureClass.PARTIAL}:
            triggers.append(ReplanTrigger.LOW_YIELD); reasons.append(f"extraction_failure:{failure.value}")
    return ReplanDecision(bool(triggers), tuple(dict.fromkeys(triggers)), tuple(dict.fromkeys(reasons)),
                          tuple(_preferred_actions(triggers)))


def _preferred_actions(triggers: Sequence[ReplanTrigger]) -> list[str]:
    actions: list[str] = []
    if ReplanTrigger.POLICY_CHANGED in triggers or ReplanTrigger.QUOTA_CHANGED in triggers:
        actions.append("revalidate_route_eligibility")
    if ReplanTrigger.METHOD_FAILED in triggers or ReplanTrigger.SOURCE_DEGRADED in triggers:
        actions.append("select_next_permitted_method")
    if ReplanTrigger.GAP in triggers:
        actions.append("generate_gap_queries")
    if ReplanTrigger.CONTRADICTION in triggers:
        actions.append("target_counterevidence_and_variant_check")
    if ReplanTrigger.FRESHNESS_EXPIRED in triggers:
        actions.append("refresh_stale_claims")
    if ReplanTrigger.CAPABILITY_CHANGED in triggers:
        actions.append("recompute_capability_fit")
    return actions


def filter_permitted_methods(methods: Sequence[MethodCandidate], failed_method_ids: Sequence[str]) -> tuple[MethodCandidate, ...]:
    failed = set(failed_method_ids)
    return tuple(m for m in methods if m.method_id not in failed)
