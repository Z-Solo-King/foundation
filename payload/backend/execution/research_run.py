from dataclasses import dataclass

from backend.intelligence.contracts import ResearchContract, ResearchPlan
from backend.intelligence.planning import create_plan


@dataclass(frozen=True)
class ResearchRun:
    run_id: str
    contract: ResearchContract
    plan: ResearchPlan
    status: str = "planned"


def create_run(run_id, contract):
    return ResearchRun(run_id, contract, create_plan(contract))


def transition(run, status):
    if status not in {"planned", "running", "completed", "failed"}:
        raise ValueError("invalid run status")
    return ResearchRun(run.run_id, run.contract, run.plan, status)
