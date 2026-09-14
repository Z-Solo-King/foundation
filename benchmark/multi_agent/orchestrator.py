from __future__ import annotations

import asyncio
import json
from collections.abc import Awaitable, Callable
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Protocol

from .models import AgentResult, AgentSpec, ProgramResult, ResearchProgram


class AgentExecutor(Protocol):
    async def __call__(self, program: ResearchProgram, agent: AgentSpec, context: dict[str, object]) -> AgentResult:
        ...


async def deterministic_executor(program: ResearchProgram, agent: AgentSpec, context: dict[str, object]) -> AgentResult:
    """Safe contract executor used for orchestration tests and dry runs.

    Real model/tool adapters are injected by callers; the scheduler itself never owns
    credentials or provider-specific network code.
    """
    await asyncio.sleep(0)
    return AgentResult.now(
        agent.agent_id,
        "completed",
        note=f"dry-run role={agent.role} program={program.program_id}",
    )


class MultiAgentCoordinator:
    """Run independent research programs concurrently with bounded agent fan-out."""

    def __init__(self, *, global_active_agents: int = 18, executor: AgentExecutor | None = None) -> None:
        if global_active_agents < 1:
            raise ValueError("global_active_agents must be positive")
        self.global_active_agents = global_active_agents
        self.executor = executor or deterministic_executor
        self._global_semaphore = asyncio.Semaphore(global_active_agents)

    async def _run_agent(
        self,
        program: ResearchProgram,
        agent: AgentSpec,
        context: dict[str, object],
    ) -> AgentResult:
        async with self._global_semaphore:
            try:
                return await self.executor(program, agent, context)
            except Exception as exc:  # adapter failures become evidence-bearing results
                return AgentResult.now(agent.agent_id, "failed", note=f"{type(exc).__name__}: {exc}")

    async def run_program(self, program: ResearchProgram, *, context: dict[str, object] | None = None) -> ProgramResult:
        started = datetime.now(timezone.utc)
        result = ProgramResult(program_id=program.program_id, lane=program.lane, slot=program.slot, started_at=started, status="running")
        shared = dict(context or {})
        shared.setdefault("program_id", program.program_id)
        shared.setdefault("question", program.question)
        per_program = asyncio.Semaphore(program.max_active_agents)

        async def limited(agent: AgentSpec) -> AgentResult:
            async with per_program:
                return await self._run_agent(program, agent, shared)

        results = await asyncio.gather(*(limited(agent) for agent in program.agent_specs))
        result.agent_results.extend(results)
        for agent_result in results:
            result.findings.extend(agent_result.findings)
            result.follow_up_questions.extend(agent_result.follow_up_questions)
        result.completed_at = datetime.now(timezone.utc)
        if all(row.status == "completed" for row in results):
            result.status = "completed"
        elif any(row.status == "completed" for row in results):
            result.status = "partial"
        elif any(row.status == "blocked" for row in results):
            result.status = "blocked"
        else:
            result.status = "failed"
        return result

    async def run_programs(self, programs: tuple[ResearchProgram, ...], *, context: dict[str, object] | None = None) -> list[ProgramResult]:
        if not programs:
            return []
        return await asyncio.gather(*(self.run_program(program, context=context) for program in programs))


class JsonlResearchReporter:
    def __init__(self, output: Path) -> None:
        self.output = output
        self.output.parent.mkdir(parents=True, exist_ok=True)

    def append(self, result: ProgramResult) -> None:
        payload = asdict(result)
        payload["started_at"] = result.started_at.isoformat()
        payload["completed_at"] = result.completed_at.isoformat() if result.completed_at else None
        for row in payload["agent_results"]:
            row["started_at"] = row["started_at"].isoformat()
            row["completed_at"] = row["completed_at"].isoformat()
        with self.output.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n")
