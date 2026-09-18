from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
import hashlib
import json


class StopDecisionReason(StrEnum):
    REQUIRED_EVIDENCE_MISSING = "required_evidence_missing"
    CONTRADICTION_REQUIRES_INVESTIGATION = "contradiction_requires_investigation"
    FRESHNESS_REQUIRES_REFRESH = "freshness_requires_refresh"
    NOVEL_EVIDENCE_WORTH_COST = "novel_evidence_worth_cost"
    REDUNDANT_EVIDENCE = "redundant_evidence"
    BUDGET_EXHAUSTED = "budget_exhausted"
    DEADLINE_EXCEEDED = "deadline_exceeded"
    NO_ACQUISITION_LANE = "no_acquisition_lane"
    SUFFICIENT_COVERAGE = "sufficient_coverage"


@dataclass(frozen=True)
class StopDecisionSnapshot:
    required_missing: int = 0
    unresolved_contradictions: int = 0
    freshness_noncompliant: int = 0
    source_novelty_milli: int = 0
    independent_corroboration: int = 0
    remaining_resource_units: int = 0
    remaining_ms: int | None = None
    acquisition_available: bool = True

    def validate(self) -> None:
        for value, name in (
            (self.required_missing, "required_missing"),
            (self.unresolved_contradictions, "unresolved_contradictions"),
            (self.freshness_noncompliant, "freshness_noncompliant"),
            (self.independent_corroboration, "independent_corroboration"),
            (self.remaining_resource_units, "remaining_resource_units"),
        ):
            if value < 0:
                raise ValueError(f"{name} must be non-negative")
        if not 0 <= self.source_novelty_milli <= 1_000:
            raise ValueError("source_novelty_milli must be between 0 and 1000")
        if self.remaining_ms is not None and self.remaining_ms < 0:
            raise ValueError("remaining_ms must be non-negative")


@dataclass(frozen=True)
class StopDecision:
    continue_research: bool
    reason: StopDecisionReason
    marginal_value_milli: int
    fingerprint: str

    @staticmethod
    def build(continue_research: bool, reason: StopDecisionReason, marginal_value_milli: int, snapshot: StopDecisionSnapshot) -> "StopDecision":
        payload = {
            "continue_research": continue_research,
            "reason": reason.value,
            "marginal_value_milli": marginal_value_milli,
            "snapshot": {
                "required_missing": snapshot.required_missing,
                "unresolved_contradictions": snapshot.unresolved_contradictions,
                "freshness_noncompliant": snapshot.freshness_noncompliant,
                "source_novelty_milli": snapshot.source_novelty_milli,
                "independent_corroboration": snapshot.independent_corroboration,
                "remaining_resource_units": snapshot.remaining_resource_units,
                "remaining_ms": snapshot.remaining_ms,
                "acquisition_available": snapshot.acquisition_available,
            },
        }
        fingerprint = hashlib.sha256(
            json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()
        return StopDecision(continue_research, reason, marginal_value_milli, fingerprint)


def decide_continuation(snapshot: StopDecisionSnapshot) -> StopDecision:
    snapshot.validate()
    if snapshot.remaining_resource_units == 0:
        return StopDecision.build(False, StopDecisionReason.BUDGET_EXHAUSTED, 0, snapshot)
    if snapshot.remaining_ms == 0:
        return StopDecision.build(False, StopDecisionReason.DEADLINE_EXCEEDED, 0, snapshot)
    if not snapshot.acquisition_available:
        return StopDecision.build(False, StopDecisionReason.NO_ACQUISITION_LANE, 0, snapshot)
    if snapshot.required_missing > 0:
        return StopDecision.build(True, StopDecisionReason.REQUIRED_EVIDENCE_MISSING, 1_000, snapshot)
    if snapshot.unresolved_contradictions > 0:
        return StopDecision.build(True, StopDecisionReason.CONTRADICTION_REQUIRES_INVESTIGATION, 900, snapshot)
    if snapshot.freshness_noncompliant > 0:
        return StopDecision.build(True, StopDecisionReason.FRESHNESS_REQUIRES_REFRESH, 800, snapshot)
    if snapshot.source_novelty_milli > 0:
        return StopDecision.build(True, StopDecisionReason.NOVEL_EVIDENCE_WORTH_COST, snapshot.source_novelty_milli, snapshot)
    if snapshot.independent_corroboration == 0:
        return StopDecision.build(False, StopDecisionReason.REDUNDANT_EVIDENCE, 0, snapshot)
    return StopDecision.build(False, StopDecisionReason.SUFFICIENT_COVERAGE, 0, snapshot)
