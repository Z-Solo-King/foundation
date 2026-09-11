"""Backward-compatible facade over the canonical research execution model.

This module contains no independent execution state or business logic.  New code
should import ``backend.execution.engine`` directly.
"""

from backend.execution.engine import ResearchRun, add_observation, create_run
from backend.execution.resources import ResourceBudget
from backend.intelligence.contracts import ResearchContract
from backend.intelligence.planning import create_plan

PipelineRun = ResearchRun


def start_run(contract: ResearchContract, run_id: str = "pipeline-compat") -> ResearchRun:
    return create_run(run_id, contract, create_plan(contract))


def attach_observation(run: ResearchRun, observation, budget: ResourceBudget) -> ResearchRun:
    return add_observation(run, observation, budget)
