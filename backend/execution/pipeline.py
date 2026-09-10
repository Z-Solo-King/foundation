from dataclasses import dataclass

from backend.intelligence.certificates import EvidenceCertificate
from backend.intelligence.claims import Claim
from backend.intelligence.contracts import ResearchContract
from backend.intelligence.observations import EvidenceSpan, Observation
from backend.intelligence.planning import create_plan
from .resources import ResourceBudget


@dataclass(frozen=True)
class ResearchRun:
    contract: ResearchContract
    plan_stages: tuple[str, ...]
    observations: tuple[Observation, ...] = ()
    claims: tuple[Claim, ...] = ()
    certificates: tuple[EvidenceCertificate, ...] = ()


def start_run(contract: ResearchContract) -> ResearchRun:
    plan = create_plan(contract)
    return ResearchRun(contract=contract, plan_stages=plan.stages)


def attach_observation(
    run: ResearchRun,
    observation: Observation,
    budget: ResourceBudget,
) -> ResearchRun:
    budget.consume_evidence()
    return ResearchRun(
        contract=run.contract,
        plan_stages=run.plan_stages,
        observations=run.observations + (observation,),
        claims=run.claims,
        certificates=run.certificates,
    )
