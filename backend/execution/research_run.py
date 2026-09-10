from dataclasses import dataclass

from backend.intelligence.contracts import ResearchContract, ResearchPlan
from backend.intelligence.planning import create_plan


@dataclass(frozen=True)
class ResearchRun:
    run_id: str
    contract: ResearchContract
    plan: ResearchPlan
    status: str = "planned"


def create_run(run_id: str, contract: ResearchContract) -> ResearchRun:
    return ResearchRun(
        run_id=run_id,
        contract=contract,
        plan=create_plan(contract),
    )


def transition(run: ResearchRun, status: str) -> ResearchRun:
    if status not in {"planned", "running", "completed", "failed"}:
        raise ValueError("invalid run status")

    return ResearchRun(
        run_id=run.run_id,
        contract=run.contract,
        plan=run.plan,
        status=status,
    )
