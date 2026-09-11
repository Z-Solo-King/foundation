"""Compatibility facade over the canonical research execution model.

New code should import ``backend.execution.engine`` directly. This module keeps
legacy imports working without maintaining a second ResearchRun implementation.
"""

from backend.execution.engine import ResearchRun, create_run as create_engine_run, transition_research
from backend.intelligence.contracts import ResearchContract
from backend.intelligence.planning import create_plan


def create_run(run_id: str, contract: ResearchContract) -> ResearchRun:
    return create_engine_run(run_id, contract, create_plan(contract))


def transition(run: ResearchRun, status: str) -> ResearchRun:
    return transition_research(run, status)


__all__ = ["ResearchRun", "create_run", "transition"]
