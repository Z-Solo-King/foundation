from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
import hashlib
import json


class PublicationOutcome(StrEnum):
    PUBLISH_COMPLETED = "publish_completed"
    PUBLISH_PARTIAL = "publish_partial"
    WITHHOLD_EXECUTION = "withhold_execution"
    WITHHOLD_EVIDENCE = "withhold_evidence"
    WITHHOLD_FRESHNESS = "withhold_freshness"
    WITHHOLD_CLAIMS = "withhold_claims"
    WITHHOLD_PROVENANCE = "withhold_provenance"
    BLOCK_POLICY = "block_policy"
    BLOCK_PRIVATE_EVIDENCE = "block_private_evidence"


_UNRESOLVED_CLAIM_STATES = frozenset({"UNVERIFIED", "UNKNOWN", "CONTRADICTED", "STALE"})
_EXECUTION_TERMINAL_STATES = frozenset({"completed", "failed", "blocked", "cancelled", "partial"})


@dataclass(frozen=True)
class PublicationGateSnapshot:
    execution_state: str
    missing_scope: int = 0
    failed_scope: int = 0
    claim_states: tuple[str, ...] = ()
    freshness_state: str = "unknown"
    evidence_integrity: bool = True
    independent_evidence: bool = True
    policy_eligible: bool = True
    provenance_complete: bool = True
    private_evidence: bool = False

    def validate(self) -> None:
        if self.execution_state not in _EXECUTION_TERMINAL_STATES:
            raise ValueError("execution_state must be terminal for publication")
        if self.missing_scope < 0 or self.failed_scope < 0:
            raise ValueError("scope counts must be non-negative")
        if self.freshness_state not in {"fresh", "stale", "unknown"}:
            raise ValueError("freshness_state is invalid")
        if any(not state.strip() for state in self.claim_states):
            raise ValueError("claim_states must contain non-empty values")


@dataclass(frozen=True)
class PublicationDecision:
    outcome: PublicationOutcome
    reason: str
    fingerprint: str

    @staticmethod
    def build(outcome: PublicationOutcome, reason: str, snapshot: PublicationGateSnapshot) -> "PublicationDecision":
        payload = {
            "outcome": outcome.value,
            "reason": reason,
            "snapshot": {
                "execution_state": snapshot.execution_state,
                "missing_scope": snapshot.missing_scope,
                "failed_scope": snapshot.failed_scope,
                "claim_states": list(snapshot.claim_states),
                "freshness_state": snapshot.freshness_state,
                "evidence_integrity": snapshot.evidence_integrity,
                "independent_evidence": snapshot.independent_evidence,
                "policy_eligible": snapshot.policy_eligible,
                "provenance_complete": snapshot.provenance_complete,
                "private_evidence": snapshot.private_evidence,
            },
        }
        fingerprint = hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
        return PublicationDecision(outcome, reason, fingerprint)


def decide_publication(snapshot: PublicationGateSnapshot) -> PublicationDecision:
    snapshot.validate()
    if snapshot.private_evidence:
        return PublicationDecision.build(
            PublicationOutcome.BLOCK_PRIVATE_EVIDENCE,
            "private evidence cannot cross the public publication boundary",
            snapshot,
        )
    if not snapshot.policy_eligible:
        return PublicationDecision.build(PublicationOutcome.BLOCK_POLICY, "publication policy denied", snapshot)
    if snapshot.execution_state in {"failed", "blocked", "cancelled"}:
        return PublicationDecision.build(PublicationOutcome.WITHHOLD_EXECUTION, "execution did not reach a publishable terminal state", snapshot)
    if not snapshot.evidence_integrity or not snapshot.independent_evidence:
        return PublicationDecision.build(PublicationOutcome.WITHHOLD_EVIDENCE, "evidence integrity or independence is incomplete", snapshot)
    if snapshot.freshness_state != "fresh":
        return PublicationDecision.build(PublicationOutcome.WITHHOLD_FRESHNESS, "freshness requirements are not satisfied", snapshot)
    if any(state.upper() in _UNRESOLVED_CLAIM_STATES for state in snapshot.claim_states):
        return PublicationDecision.build(PublicationOutcome.WITHHOLD_CLAIMS, "claim support contains unresolved or contradictory states", snapshot)
    if not snapshot.provenance_complete:
        return PublicationDecision.build(PublicationOutcome.WITHHOLD_PROVENANCE, "publication provenance is incomplete", snapshot)
    if snapshot.execution_state == "partial" or snapshot.missing_scope > 0 or snapshot.failed_scope > 0:
        return PublicationDecision.build(PublicationOutcome.PUBLISH_PARTIAL, "publication is limited by incomplete execution scope", snapshot)
    return PublicationDecision.build(PublicationOutcome.PUBLISH_COMPLETED, "all publication gates satisfied", snapshot)
