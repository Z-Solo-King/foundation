"""Canonical bounded research execution state and lifecycle."""

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import StrEnum
from typing import Any

from backend.intelligence.contracts import ResearchContract, ResearchPlan
from backend.intelligence.observations import Observation
from backend.intelligence.claims import Claim
from backend.intelligence.lineage import SourceLineage
from backend.intelligence.verifier import EvidenceVerifier, ClaimStatus
from backend.execution.resources import ResourceBudget


class ResearchLifecycle(StrEnum):
    """Canonical execution lifecycle shared by run and receipt boundaries."""

    PLANNED = "planned"
    RUNNING = "running"
    COMPLETED = "completed"
    PARTIAL = "partial"
    FAILED = "failed"
    BLOCKED = "blocked"
    CANCELLED = "cancelled"


TERMINAL_RESEARCH_LIFECYCLES = frozenset(
    {
        ResearchLifecycle.COMPLETED,
        ResearchLifecycle.PARTIAL,
        ResearchLifecycle.FAILED,
        ResearchLifecycle.BLOCKED,
        ResearchLifecycle.CANCELLED,
    }
)


@dataclass(frozen=True)
class ResearchRun:
    run_id: str
    contract: ResearchContract
    plan: ResearchPlan
    status: ResearchLifecycle = ResearchLifecycle.PLANNED
    observations: tuple[Observation, ...] = ()
    claims: tuple[Claim, ...] = ()
    verified_claims: tuple[tuple[Claim, Any], ...] = ()
    started_at: datetime | None = None
    completed_at: datetime | None = None

    def __post_init__(self) -> None:
        try:
            lifecycle = self.status if isinstance(self.status, ResearchLifecycle) else ResearchLifecycle(self.status)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"invalid run status: {self.status}") from exc
        object.__setattr__(self, "status", lifecycle)

    @property
    def plan_stages(self) -> tuple[str, ...]:
        """Compatibility view; execution owns the canonical ResearchPlan."""
        return self.plan.stages


def create_run(run_id: str, contract: ResearchContract, plan: ResearchPlan) -> ResearchRun:
    return ResearchRun(run_id, contract, plan)


def _transition_terminal(run: ResearchRun, status: ResearchLifecycle) -> ResearchRun:
    if run.status is not ResearchLifecycle.RUNNING:
        raise ValueError(f"invalid or unsupported terminal transition from {run.status}")
    if status not in TERMINAL_RESEARCH_LIFECYCLES:
        raise ValueError(f"invalid terminal status {status}")
    return ResearchRun(
        run.run_id,
        run.contract,
        run.plan,
        status,
        run.observations,
        run.claims,
        run.verified_claims,
        run.started_at,
        datetime.now(timezone.utc),
    )


def start_research(run: ResearchRun) -> ResearchRun:
    if run.status is not ResearchLifecycle.PLANNED:
        raise ValueError(f"cannot start run with status {run.status}")
    return ResearchRun(
        run.run_id,
        run.contract,
        run.plan,
        ResearchLifecycle.RUNNING,
        run.observations,
        run.claims,
        run.verified_claims,
        datetime.now(timezone.utc),
        run.completed_at,
    )


def add_observation(run: ResearchRun, obs: Observation, budget: ResourceBudget) -> ResearchRun:
    budget.consume_evidence()
    return ResearchRun(
        run.run_id,
        run.contract,
        run.plan,
        run.status,
        run.observations + (obs,),
        run.claims,
        run.verified_claims,
        run.started_at,
        run.completed_at,
    )


def add_claim(run: ResearchRun, claim: Claim) -> ResearchRun:
    return ResearchRun(
        run.run_id,
        run.contract,
        run.plan,
        run.status,
        run.observations,
        run.claims + (claim,),
        run.verified_claims,
        run.started_at,
        run.completed_at,
    )


def verify_and_add_claim(
    run: ResearchRun,
    claim: Claim,
    evidence_certs: tuple,
    verifier: EvidenceVerifier,
    lineages: dict[str, SourceLineage],
) -> ResearchRun:
    """Verify a claim against observations and prior claims and add to verified set."""
    obs_dict = {o.observation_id: o for o in run.observations}
    result = verifier.verify_claim(
        claim,
        evidence_certs,
        obs_dict,
        lineages,
        other_claims=run.claims,
    )
    return ResearchRun(
        run.run_id,
        run.contract,
        run.plan,
        run.status,
        run.observations,
        run.claims,
        run.verified_claims + ((claim, result),),
        run.started_at,
        run.completed_at,
    )


def complete_research(run: ResearchRun, success: bool = True) -> ResearchRun:
    if run.status is not ResearchLifecycle.RUNNING:
        raise ValueError(f"cannot complete run with status {run.status}")
    return _transition_terminal(
        run,
        ResearchLifecycle.COMPLETED if success else ResearchLifecycle.FAILED,
    )


def transition_research(run: ResearchRun, status: ResearchLifecycle | str) -> ResearchRun:
    """Apply the canonical lifecycle algebra without creating a second run model."""
    try:
        target = status if isinstance(status, ResearchLifecycle) else ResearchLifecycle(status)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"invalid run status: {status}") from exc

    if target is run.status:
        return run
    if run.status is ResearchLifecycle.PLANNED and target is ResearchLifecycle.RUNNING:
        return start_research(run)
    if run.status is ResearchLifecycle.RUNNING and target in TERMINAL_RESEARCH_LIFECYCLES:
        return _transition_terminal(run, target)
    raise ValueError(f"invalid or unsupported run transition: {run.status} -> {target}")


def summarize_research(run: ResearchRun) -> dict[str, Any]:
    if not run.verified_claims:
        return {
            "run_id": run.run_id,
            "status": run.status,
            "question": run.contract.question,
            "observations": len(run.observations),
            "claims_verified": 0,
            "corroborated_claims": 0,
            "contradicted_claims": 0,
            "findings": [],
        }
    corroborated = sum(1 for _, result in run.verified_claims if result.status == ClaimStatus.CORROBORATED)
    contradicted = sum(1 for _, result in run.verified_claims if result.status == ClaimStatus.CONTRADICTED)
    findings = [
        {
            "claim": claim.text,
            "status": result.status,
            "supporting_evidence": len(result.supporting_evidence),
            "independent_corroboration": result.independent_corroboration_count,
            "reasons": list(result.reasons),
        }
        for claim, result in run.verified_claims
    ]
    return {
        "run_id": run.run_id,
        "status": run.status,
        "question": run.contract.question,
        "observations": len(run.observations),
        "claims_verified": len(run.verified_claims),
        "corroborated_claims": corroborated,
        "contradicted_claims": contradicted,
        "findings": findings,
    }
