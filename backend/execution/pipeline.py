from dataclasses import dataclass

from backend.intelligence.contracts import ResearchContract
from backend.intelligence.observations import Observation
from backend.intelligence.planning import create_plan
from .resources import ResourceBudget


@dataclass(frozen=True)
class PipelineRun:
    contract: ResearchContract
    plan_stages: tuple[str, ...]
    observations: tuple[Observation, ...] = ()

    @property
    def plan(self):
        """Compatibility view exposing the generated plan."""
        return create_plan(self.contract)


def start_run(contract):
    return PipelineRun(contract, create_plan(contract).stages)


def attach_observation(run, observation, budget: ResourceBudget):
    budget.consume_evidence()
    return PipelineRun(run.contract, run.plan_stages, run.observations + (observation,))
