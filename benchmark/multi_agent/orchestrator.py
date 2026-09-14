from __future__ import annotations

import asyncio
import json
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Protocol

from .models import AgentResult, AgentSpec, CapacityComparison, ProgramResult, ResearchProgram


class AgentExecutor(Protocol):
    async def __call__(self, program: ResearchProgram, agent: AgentSpec, context: dict[str, object]) -> AgentResult:
        ...


async def deterministic_executor(program: ResearchProgram, agent: AgentSpec, context: dict[str, object]) -> AgentResult:
    await asyncio.sleep(0)
    return AgentResult.now(agent.agent_id, "completed", note=f"dry-run role={agent.role} program={program.program_id}")


class MultiAgentCoordinator:
    """Dynamic bounded executor: one program may use 1-10 agents; all programs share one global cap."""

    def __init__(self, *, global_active_agents: int = 20, executor: AgentExecutor | None = None) -> None:
        if not 1 <= global_active_agents <= 20:
            raise ValueError("global_active_agents must be between 1 and 20")
        self.global_active_agents = global_active_agents
        self.executor = executor or deterministic_executor
        self._global_semaphore = asyncio.Semaphore(global_active_agents)

    @staticmethod
    def _select_agents(program: ResearchProgram, budget: int) -> tuple[AgentSpec, ...]:
        budget = max(1, min(budget, len(program.agent_specs), 10))
        finals = [a for a in program.agent_specs if a.role in {"reconciler", "evaluator"}]
        evidence = [a for a in program.agent_specs if a.role not in {"reconciler", "evaluator"}]
        evidence.sort(key=lambda a: (-a.priority, a.agent_id))
        if budget >= len(finals):
            selected = evidence[: budget - len(finals)] + finals
        else:
            selected = sorted(program.agent_specs, key=lambda a: (-a.priority, a.agent_id))[:budget]
        return tuple(selected)

    async def _run_agent(self, program: ResearchProgram, agent: AgentSpec, context: dict[str, object]) -> AgentResult:
        async with self._global_semaphore:
            started = datetime.now(timezone.utc)
            try:
                result = await self.executor(program, agent, context)
                return result
            except Exception as exc:
                return AgentResult(agent.agent_id, "failed", started, datetime.now(timezone.utc), note=f"{type(exc).__name__}: {exc}")

    async def _run_phase(self, program: ResearchProgram, agents: tuple[AgentSpec, ...], context: dict[str, object]) -> list[AgentResult]:
        return list(await asyncio.gather(*(self._run_agent(program, agent, context) for agent in agents)))

    async def run_program(
        self,
        program: ResearchProgram,
        *,
        context: dict[str, object] | None = None,
        agent_budget: int | None = None,
    ) -> ProgramResult:
        budget = program.agent_budget_hint if agent_budget is None else agent_budget
        selected = self._select_agents(program, budget)
        started = datetime.now(timezone.utc)
        result = ProgramResult(
            program_id=program.program_id,
            lane=program.lane,
            slot=program.slot,
            started_at=started,
            status="running",
            allocated_agents=len(selected),
        )
        shared = dict(context or {})
        shared.update({"program_id": program.program_id, "question": program.question, "allocated_agents": len(selected)})

        evidence_agents = tuple(a for a in selected if a.role not in {"reconciler", "evaluator"})
        final_agents = tuple(a for a in selected if a.role in {"reconciler", "evaluator"})
        evidence_results = await self._run_phase(program, evidence_agents, shared)
        result.agent_results.extend(evidence_results)
        result.findings.extend(finding for row in evidence_results for finding in row.findings)
        result.follow_up_questions.extend(question for row in evidence_results for question in row.follow_up_questions)

        if final_agents:
            synthesis = dict(shared)
            synthesis["evidence_results"] = [asdict(row) for row in evidence_results]
            final_results = await self._run_phase(program, final_agents, synthesis)
            result.agent_results.extend(final_results)
            result.findings.extend(finding for row in final_results for finding in row.findings)
            result.follow_up_questions.extend(question for row in final_results for question in row.follow_up_questions)

        result.completed_at = datetime.now(timezone.utc)
        statuses = [row.status for row in result.agent_results]
        if statuses and all(status == "completed" for status in statuses):
            result.status = "completed"
        elif any(status == "completed" for status in statuses):
            result.status = "partial"
        elif any(status == "blocked" for status in statuses):
            result.status = "blocked"
        else:
            result.status = "failed"
        return result

    async def run_programs(self, programs: tuple[ResearchProgram, ...], *, context: dict[str, object] | None = None) -> list[ProgramResult]:
        scheduler = DynamicResearchScheduler(self)
        return await scheduler.run(programs, context=context)


class DynamicResearchScheduler:
    """Pack research programs into a hard global agent budget and refill capacity immediately."""

    CATEGORY_BUDGETS = {
        "acquisition": 6,
        "mapper": 7,
        "chatbot": 8,
        "search": 5,
        "models": 5,
        "agents": 7,
        "architecture": 7,
        "infrastructure": 6,
        "performance": 6,
        "alternatives": 6,
        "evaluation": 4,
    }

    def __init__(self, coordinator: MultiAgentCoordinator) -> None:
        self.coordinator = coordinator

    def estimate_agents(self, program: ResearchProgram) -> int:
        return max(1, min(10, self.CATEGORY_BUDGETS.get(program.category, program.agent_budget_hint)))

    @staticmethod
    def _priority(program: ResearchProgram) -> tuple[int, int, str]:
        return (program.slot, program.agent_budget_hint, program.program_id)

    async def run(self, programs: tuple[ResearchProgram, ...], *, context: dict[str, object] | None = None) -> list[ProgramResult]:
        pending = list(sorted(programs, key=self._priority))
        running: dict[asyncio.Task[ProgramResult], tuple[ResearchProgram, int]] = {}
        used = 0
        results: list[ProgramResult] = []

        while pending or running:
            made_progress = True
            while pending and made_progress:
                made_progress = False
                for index, program in enumerate(pending):
                    needed = self.estimate_agents(program)
                    if needed <= self.coordinator.global_active_agents - used:
                        pending.pop(index)
                        task = asyncio.create_task(
                            self.coordinator.run_program(program, context=context, agent_budget=needed)
                        )
                        running[task] = (program, needed)
                        used += needed
                        made_progress = True
                        break

            if not running:
                # A valid program is always <=10 and the global limit is >=1.
                program = pending.pop(0)
                needed = min(self.estimate_agents(program), self.coordinator.global_active_agents, 10)
                task = asyncio.create_task(self.coordinator.run_program(program, context=context, agent_budget=needed))
                running[task] = (program, needed)
                used += needed

            done, _ = await asyncio.wait(tuple(running), return_when=asyncio.FIRST_COMPLETED)
            for task in done:
                program, reserved = running.pop(task)
                used -= reserved
                results.append(task.result())

        return results


class CapacityExperiment:
    """Run the same research at two agent budgets to measure marginal value, time and duplication."""

    def __init__(self, coordinator: MultiAgentCoordinator) -> None:
        self.coordinator = coordinator

    async def compare(
        self,
        program: ResearchProgram,
        *,
        low_agents: int = 5,
        high_agents: int = 10,
        context: dict[str, object] | None = None,
    ) -> CapacityComparison:
        if not 1 <= low_agents < high_agents <= 10:
            raise ValueError("capacity comparison requires 1 <= low < high <= 10")
        low = await self.coordinator.run_program(program, context={**(context or {}), "capacity_arm": low_agents}, agent_budget=low_agents)
        high = await self.coordinator.run_program(program, context={**(context or {}), "capacity_arm": high_agents}, agent_budget=high_agents)
        return CapacityComparison(program.program_id, low, high)


class JsonlResearchReporter:
    def __init__(self, output: Path) -> None:
        self.output = output
        self.output.parent.mkdir(parents=True, exist_ok=True)

    def append(self, result: ProgramResult) -> None:
        payload = asdict(result)
        payload["started_at"] = result.started_at.isoformat()
        payload["completed_at"] = result.completed_at.isoformat() if result.completed_at else None
        payload["measurement"] = result.measurement()
        for row in payload["agent_results"]:
            row["started_at"] = row["started_at"].isoformat()
            row["completed_at"] = row["completed_at"].isoformat()
        with self.output.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n")

    def append_capacity_comparison(self, comparison: CapacityComparison) -> None:
        with self.output.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps({"schema": "multi-agent-capacity/v1", **comparison.to_dict()}, ensure_ascii=False, sort_keys=True) + "\n")
