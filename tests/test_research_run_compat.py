import pytest

from backend.execution.engine import ResearchRun, create_run as create_engine_run
from backend.execution.research_run import create_run, transition
from backend.intelligence.contracts import ResearchContract
from backend.intelligence.planning import create_plan


def test_compatibility_facade_returns_canonical_type():
    contract = ResearchContract(question="test")
    run = create_run("compat", contract)
    assert isinstance(run, ResearchRun)
    assert run.status == "planned"


def test_compatibility_transitions_preserve_canonical_state():
    contract = ResearchContract(question="test")
    run = create_engine_run("compat", contract, create_plan(contract))
    running = transition(run, "running")
    completed = transition(running, "completed")
    assert running.status == "running"
    assert running.started_at is not None
    assert completed.status == "completed"
    assert completed.completed_at is not None


def test_invalid_lifecycle_transition_is_rejected():
    contract = ResearchContract(question="test")
    run = create_engine_run("compat", contract, create_plan(contract))
    with pytest.raises(ValueError):
        transition(run, "completed")
