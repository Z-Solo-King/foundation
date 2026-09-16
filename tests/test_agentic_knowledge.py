from datetime import datetime, timezone

import pytest

from backend.intelligence.agentic import ResearchAgent, ResearchTask, TaskObservation, research
from backend.intelligence.contracts import ResearchContract
from backend.intelligence.evidence import EvidenceKnowledgeStore, EvidenceRecord
from backend.memory import ResearchMemory

NOW = datetime(2026, 9, 13, tzinfo=timezone.utc)


def test_agent_validation_and_terminal_states():
    with pytest.raises(ValueError):
        ResearchAgent(max_iterations=0)
    agent = ResearchAgent(max_iterations=2)
    state = agent.create_state(ResearchContract(question="test", depth="quick"))
    assert not hasattr(agent, "_reuse")
    finished = agent.step(state)
    assert finished.status == "blocked"
    done = agent.step(finished)
    assert done == finished

    executor_agent = ResearchAgent(executor=lambda task, store: TaskObservation(task.task_id, "completed"), max_iterations=32)
    no_tasks = executor_agent.step(state.__class__(question=state.question, plan=state.plan, tasks=(), iterations=0))
    assert no_tasks.status == "completed"
    blocked_state = executor_agent.step(state.__class__(question=state.question, plan=state.plan, tasks=(), failed=("x",), iterations=0))
    assert blocked_state.status == "blocked"
    maxed = state.__class__(question=state.question, plan=state.plan, tasks=state.tasks, iterations=32)
    assert executor_agent.step(maxed).status == "blocked"
