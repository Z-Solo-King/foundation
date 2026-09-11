"""Complete research execution pipeline.

Connects planner -> acquisition -> observation -> evidence -> verification -> synthesis
as one bounded vertical slice. All stages respect resource budgets and fail-closed constraints.
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from backend.intelligence.contracts import ResearchContract, ResearchPlan
from backend.intelligence.observations import Observation
from backend.intelligence.claims import Claim
from backend.intelligence.lineage import SourceLineage
from backend.intelligence.verifier import EvidenceVerifier, ClaimStatus
from backend.execution.resources import ResourceBudget


@dataclass(frozen=True)
class ResearchRun:
    """Complete research run with contract, plan, and intermediate state."""
    run_id: str
    contract: ResearchContract
    plan: ResearchPlan
    status: str = "planned"  # planned, running, completed, failed
    observations: tuple[Observation, ...] = ()
    claims: tuple[Claim, ...] = ()
    verified_claims: tuple[tuple[Claim, Any], ...] = ()  # (Claim, VerificationResult)
    started_at: datetime | None = None
    completed_at: datetime | None = None


def create_run(run_id: str, contract: ResearchContract, plan: ResearchPlan) -> ResearchRun:
    """Create a new research run."""
    return ResearchRun(run_id, contract, plan)


def start_research(run: ResearchRun) -> ResearchRun:
    """Transition run to 'running' status."""
    if run.status != "planned":
        raise ValueError(f"cannot start run with status {run.status}")
    return ResearchRun(
        run.run_id,
        run.contract,
        run.plan,
        "running",
        run.observations,
        run.claims,
        run.verified_claims,
        datetime.now(timezone.utc),
        run.completed_at,
    )


def add_observation(run: ResearchRun, obs: Observation, budget: ResourceBudget) -> ResearchRun:
    """Add an observation to the run and consume evidence budget."""
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
    """Add a candidate claim to the run."""
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
    """Transition run to completed or failed status."""
    if run.status != "running":
        raise ValueError(f"cannot complete run with status {run.status}")
    return ResearchRun(
        run.run_id,
        run.contract,
        run.plan,
        "completed" if success else "failed",
        run.observations,
        run.claims,
        run.verified_claims,
        run.started_at,
        datetime.now(timezone.utc),
    )


def summarize_research(run: ResearchRun) -> dict[str, Any]:
    """Generate summary of research run."""
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

    corroborated = sum(
        1 for _, result in run.verified_claims
        if result.status == ClaimStatus.CORROBORATED
    )
    contradicted = sum(
        1 for _, result in run.verified_claims
        if result.status == ClaimStatus.CONTRADICTED
    )

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
