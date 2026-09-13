"""Replay identity for deterministic planner behavior."""
from __future__ import annotations

from dataclasses import dataclass
import hashlib

from .planner_models import TaskPlan
from .planner_runtime import canonical_json, plan_fingerprint


@dataclass(frozen=True)
class ReplayBundle:
    contract_fingerprint: str
    plan_fingerprint: str
    capability_version: str
    policy_version: str
    source_profile_version: str
    quota_version: str
    freshness_epoch: str
    input_fingerprint: str
    planner_version: str
    created_at: str


def fingerprint_inputs(
    contract: object,
    capability_version: str,
    policy_version: str,
    source_profile_version: str,
    quota_version: str = "",
    freshness_epoch: str = "",
) -> str:
    payload = {
        "contract": contract,
        "capability_version": capability_version,
        "policy_version": policy_version,
        "source_profile_version": source_profile_version,
        "quota_version": quota_version,
        "freshness_epoch": freshness_epoch,
    }
    return hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()


def make_replay_bundle(
    contract: object,
    plan: TaskPlan,
    *,
    capability_version: str,
    policy_version: str,
    source_profile_version: str,
    planner_version: str,
    created_at: str,
    quota_version: str = "",
    freshness_epoch: str = "",
) -> ReplayBundle:
    contract_fp = hashlib.sha256(canonical_json(contract).encode("utf-8")).hexdigest()
    return ReplayBundle(
        contract_fingerprint=contract_fp,
        plan_fingerprint=plan_fingerprint(plan),
        capability_version=capability_version,
        policy_version=policy_version,
        source_profile_version=source_profile_version,
        quota_version=quota_version,
        freshness_epoch=freshness_epoch,
        input_fingerprint=fingerprint_inputs(
            contract,
            capability_version,
            policy_version,
            source_profile_version,
            quota_version,
            freshness_epoch,
        ),
        planner_version=planner_version,
        created_at=created_at,
    )


def replay_compatible(
    bundle: ReplayBundle,
    *,
    capability_version: str,
    policy_version: str,
    source_profile_version: str,
    quota_version: str = "",
    freshness_epoch: str = "",
) -> bool:
    return (
        bundle.capability_version == capability_version
        and bundle.policy_version == policy_version
        and bundle.source_profile_version == source_profile_version
        and bundle.quota_version == quota_version
        and bundle.freshness_epoch == freshness_epoch
    )
