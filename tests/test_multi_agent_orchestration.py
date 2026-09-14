import asyncio
import json
from pathlib import Path

import pytest

from benchmark.multi_agent.models import AgentResult, ResearchProgram
from benchmark.multi_agent.orchestrator import DynamicResearchScheduler, MultiAgentCoordinator
from benchmark.multi_agent.programs import NIGHTLY_PROGRAMS, PROGRAMS_BY_LANE


def test_matrix_and_dynamic_budget_contract():
    assert len(NIGHTLY_PROGRAMS) == 24
    assert all(len(PROGRAMS_BY_LANE[lane]) == 8 for lane in range(3))
    assert all(len(program.agent_specs) == 10 for program in NIGHTLY_PROGRAMS)
    assert all(1 <= program.agent_budget_hint <= 10 for program in NIGHTLY_PROGRAMS)


def test_program_questions_and_agents_are_unique():
    assert len({program.question for program in NIGHTLY_PROGRAMS}) == 24
    assert len({agent.agent_id for program in NIGHTLY_PROGRAMS for agent in program.agent_specs}) == 240


def test_program_model_guards():
    with pytest.raises(ValueError):
        ResearchProgram("x", 9, 0, "x", "x", "x", NIGHTLY_PROGRAMS[0].agent_specs)
    with pytest.raises(ValueError):
        ResearchProgram("x", 0, 0, "x", "x", "x", NIGHTLY_PROGRAMS[0].agent_specs, 11)


@pytest.mark.asyncio
async def test_scheduler_packs_variable_research_under_global_twenty():
    active = 0
    maximum = 0

    async def executor(program, agent, context):
        nonlocal active, maximum
        active += 1
        maximum = max(maximum, active)
        await asyncio.sleep(0.01)
        active -= 1
        return AgentResult.now(agent.agent_id, "completed", note=program.title)

    coordinator = MultiAgentCoordinator(global_active_agents=20, executor=executor)
    results = await DynamicResearchScheduler(coordinator).run(tuple(NIGHTLY_PROGRAMS[:4]))
    assert len(results) == 4
    assert all(result.status == "completed" for result in results)
    assert maximum <= 20
    assert all(1 <= result.allocated_agents <= 10 for result in results)


@pytest.mark.asyncio
async def test_extra_agents_change_measured_capacity():
    async def executor(program, agent, context):
        await asyncio.sleep(0.005)
        finding = {"claim": f"{program.program_id}:{agent.role}", "source_url": f"https://example.test/{agent.role}"}
        return AgentResult.now(agent.agent_id, "completed", note="measurement") if agent.role == "reconciler" else AgentResult(
            agent_id=agent.agent_id,
            status="completed",
            started_at=AgentResult.now(agent.agent_id, "completed").started_at,
            completed_at=AgentResult.now(agent.agent_id, "completed").completed_at,
            findings=(finding,),
        )

    coordinator = MultiAgentCoordinator(global_active_agents=20, executor=executor)
    low = await coordinator.run_program(NIGHTLY_PROGRAMS[0], agent_budget=5)
    high = await coordinator.run_program(NIGHTLY_PROGRAMS[0], agent_budget=10)
    assert low.allocated_agents == 5
    assert high.allocated_agents == 10
    assert high.measurement()["wall_clock_seconds"] >= 0
    assert high.measurement()["agent_seconds"] >= low.measurement()["agent_seconds"]


@pytest.mark.asyncio
async def test_adapter_failure_isolated_to_agent_and_program_partial():
    async def executor(program, agent, context):
        if agent.role == "adversarial":
            raise RuntimeError("adapter unavailable")
        return AgentResult.now(agent.agent_id, "completed")

    coordinator = MultiAgentCoordinator(global_active_agents=20, executor=executor)
    result = await coordinator.run_program(NIGHTLY_PROGRAMS[0], agent_budget=10)
    assert result.status == "partial"
    assert result.failed_agents == 1
    assert result.completed_agents == 9


def test_measurement_is_json_serializable(tmp_path: Path):
    payload = {"schema": "multi-agent-capacity/v1", "measurement": NIGHTLY_PROGRAMS[0].agent_budget_hint}
    path = tmp_path / "result.jsonl"
    path.write_text(json.dumps(payload) + "\n", encoding="utf-8")
    assert json.loads(path.read_text(encoding="utf-8"))["schema"] == "multi-agent-capacity/v1"
