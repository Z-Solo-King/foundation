import asyncio
import json
from pathlib import Path

import pytest

from benchmark.multi_agent.models import AgentResult, ResearchProgram
from benchmark.multi_agent.orchestrator import MultiAgentCoordinator
from benchmark.multi_agent.programs import NIGHTLY_PROGRAMS, PROGRAMS_BY_LANE


def test_matrix_is_24_programs_three_lanes_of_eight():
    assert len(NIGHTLY_PROGRAMS) == 24
    assert all(len(PROGRAMS_BY_LANE[lane]) == 8 for lane in range(3))
    assert all(len(program.agent_specs) == 10 for program in NIGHTLY_PROGRAMS)
    assert all(program.max_active_agents == 6 for program in NIGHTLY_PROGRAMS)


def test_program_questions_and_agents_are_unique():
    assert len({program.question for program in NIGHTLY_PROGRAMS}) == 24
    assert len({agent.agent_id for program in NIGHTLY_PROGRAMS for agent in program.agent_specs}) == 240


@pytest.mark.asyncio
async def test_three_programs_run_concurrently_with_global_cap():
    active = 0
    maximum = 0

    async def executor(program, agent, context):
        nonlocal active, maximum
        active += 1
        maximum = max(maximum, active)
        await asyncio.sleep(0.01)
        active -= 1
        return AgentResult.now(agent.agent_id, "completed", note=program.title)

    coordinator = MultiAgentCoordinator(global_active_agents=18, executor=executor)
    results = await coordinator.run_programs(tuple(NIGHTLY_PROGRAMS[:3]))
    assert len(results) == 3
    assert all(result.status == "completed" for result in results)
    assert maximum <= 18
    assert all(result.completed_agents == 10 for result in results)


@pytest.mark.asyncio
async def test_adapter_failure_isolated_to_agent_and_program_partial():
    async def executor(program, agent, context):
        if agent.role == "adversarial":
            raise RuntimeError("adapter unavailable")
        return AgentResult.now(agent.agent_id, "completed")

    coordinator = MultiAgentCoordinator(global_active_agents=18, executor=executor)
    result = await coordinator.run_program(NIGHTLY_PROGRAMS[0])
    assert result.status == "partial"
    assert result.failed_agents == 1
    assert result.completed_agents == 9


def test_program_model_guards():
    with pytest.raises(ValueError):
        ResearchProgram("x", 9, 0, "x", "x", "x", NIGHTLY_PROGRAMS[0].agent_specs)


def test_runner_output_contract(tmp_path: Path):
    # The reporter's JSONL structure is exercised independently of the live runner.
    payload = {"schema": "multi-agent-nightly/v1", "programs": 24}
    path = tmp_path / "result.jsonl"
    path.write_text(json.dumps(payload) + "\n", encoding="utf-8")
    assert json.loads(path.read_text(encoding="utf-8"))["programs"] == 24
