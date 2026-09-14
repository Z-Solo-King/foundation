import asyncio
from datetime import datetime, timezone

import pytest

from benchmark.multi_agent.models import AgentResult, CapacityComparison
from benchmark.multi_agent.orchestrator import (
    CapacityExperiment,
    DynamicResearchScheduler,
    MultiAgentCoordinator,
)
from benchmark.multi_agent.programs import NIGHTLY_PROGRAMS


@pytest.mark.asyncio
async def test_dynamic_scheduler_packs_to_global_20_and_refills_capacity():
    active = 0
    maximum = 0
    started: list[str] = []

    async def executor(program, agent, context):
        nonlocal active, maximum
        active += 1
        maximum = max(maximum, active)
        started.append(program.program_id)
        await asyncio.sleep(0.01 if program.program_id == "fast" else 0.03)
        active -= 1
        return AgentResult.now(agent.agent_id, "completed")

    coordinator = MultiAgentCoordinator(global_active_agents=20, executor=executor)
    programs = tuple(
        NIGHTLY_PROGRAMS[index]
        for index in (0, 8, 12, 16)
    )
    scheduler = DynamicResearchScheduler(coordinator)
    scheduler.CATEGORY_BUDGETS = {
        **scheduler.CATEGORY_BUDGETS,
        programs[0].category: 10,
    }
    results = await scheduler.run(programs)
    assert len(results) == 4
    assert maximum <= 20
    assert sum(result.allocated_agents for result in results) >= 20


def test_program_budget_hints_are_bounded_and_not_hard_caps():
    assert all(1 <= program.agent_budget_hint <= 10 for program in NIGHTLY_PROGRAMS)
    assert {program.agent_budget_hint for program in NIGHTLY_PROGRAMS} >= {4, 5, 6, 7, 8}
    assert all(program.max_active_agents == program.agent_budget_hint for program in NIGHTLY_PROGRAMS)


def test_program_measurement_captures_time_and_quality():
    started = datetime(2026, 9, 14, 12, 0, tzinfo=timezone.utc)
    finished = datetime(2026, 9, 14, 12, 5, tzinfo=timezone.utc)
    result = NIGHTLY_PROGRAMS[0]
    from benchmark.multi_agent.models import ProgramResult

    measured = ProgramResult(
        program_id=result.program_id,
        lane=result.lane,
        slot=result.slot,
        started_at=started,
        completed_at=finished,
        status="completed",
        allocated_agents=5,
        agent_results=[
            AgentResult(
                agent_id="a",
                status="completed",
                started_at=started,
                completed_at=finished,
                findings=({"claim": "x", "source_url": "https://one.example", "answer_quality": 8.0},),
            )
        ],
        findings=[
            {"claim": "x", "source_url": "https://one.example", "answer_quality": 8.0},
            {"claim": "y", "source_url": "https://two.example", "answer_quality": 9.0},
        ],
    )
    metrics = measured.measurement()
    assert metrics["wall_clock_seconds"] == 300.0
    assert metrics["allocated_agents"] == 5
    assert metrics["unique_sources"] == 2
    assert metrics["answer_quality_0_to_10"] == 8.5


@pytest.mark.asyncio
async def test_capacity_experiment_reports_marginal_delta():
    async def executor(program, agent, context):
        quality = float(context["capacity_arm"])
        return AgentResult.now(
            agent.agent_id,
            "completed",
            note="experiment",
        ).__class__(
            agent_id=agent.agent_id,
            status="completed",
            started_at=datetime.now(timezone.utc),
            completed_at=datetime.now(timezone.utc),
            findings=({"claim": agent.role, "source_url": f"https://{agent.role}.example", "answer_quality": quality},),
        )

    coordinator = MultiAgentCoordinator(global_active_agents=20, executor=executor)
    comparison = await CapacityExperiment(coordinator).compare(NIGHTLY_PROGRAMS[0], low_agents=5, high_agents=10)
    assert isinstance(comparison, CapacityComparison)
    report = comparison.to_dict()
    assert report["low"]["allocated_agents"] == 5
    assert report["high"]["allocated_agents"] == 10
    assert report["delta_answer_quality_0_to_10"] == 5.0


def test_global_capacity_is_hard_bounded():
    with pytest.raises(ValueError):
        MultiAgentCoordinator(global_active_agents=21)
