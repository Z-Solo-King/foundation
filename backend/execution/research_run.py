"""Compatibility facade over the canonical research execution model.

New code should import ``backend.execution.engine`` directly. This module keeps
legacy imports working without maintaining a second ResearchRun implementation.
"""

from backend.execution.engine import ResearchRun
from backend.execution.engine import complete_research, create_run as create_engine_run, start_research
from backend.intelligence.contracts import ResearchContract
from backend.intelligence.planning import create_plan


def create_run(run_id: str, contract: ResearchContract) -> ResearchRun:
    return create_engine_run(run_id, contract, create_plan(contract))


def transition(run: ResearchRun, status: str) -> ResearchRun:
    if status == "planned" and run.status == "planned":
        return run
    if status == "running":
        return start_research(run)
    if status == "completed":
        return complete_research(run, success=True)
    if status == "failed":
        return complete_research(run, success=False)
    raise ValueError(f"invalid or unsupported run transition: {run.status} -> {status}")


__all__ = ["ResearchRun", "create_run", "transition"]
