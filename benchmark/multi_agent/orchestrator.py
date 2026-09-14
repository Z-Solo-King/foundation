from __future__ import annotations

import asyncio
import json
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
    return AgentResult.now(agent.agent_id, "completed", note=f"dry-run role={agent.role} program={program.program_id}")


class MultiAgentCoordinator:
    """Run three-way parallel research with an 8-agent evidence phase plus reconciliation/evaluation."""

    def __init__(self, *, global_active_agents: int = 18, executor: AgentExecutor | None = None) -> None:
        if global_active_agents < 1:
            raise ValueError("global_active_agents must be positive")
        self.global_active_agents = global_active_agents
        self.executor = executor or deterministic_executor
        self._global_semaphore = asyncio.Semaphore(global_active_agents)

    async def _run_agent(self, program: ResearchProgram, agent: AgentSpec, context: dict[str, object]) -> AgentResult:
        async with self._global_semaphore:
            try:
                return await self.executor(program, agent, context)
            except Exception as exc:
                return AgentResult.now(agent.agent_id, "failed", note=f"{type(exc).__name__}: {exc}")

    async def _run_parallel_phase(
        self,
        program: ResearchProgram,
        agents: tuple[AgentSpec, ...],
        context: dict[str, object],
    ) -> list[AgentResult]:
        per_program = asyncio.Semaphore(program.max_active_agents)

        async def limited(agent: AgentSpec) -> AgentResult:
            async with per_program:
                return await self._run_agent(program, agent, context)

        return list(await asyncio.gather(*(limited(agent) for agent in agents)))

    async def run_program(self, program: ResearchProgram, *, context: dict[str, object] | None = None) -> ProgramResult:
        started = datetime.now(timezone.utc)
        result = ProgramResult(program_id=program.program_id, lane=program.lane, slot=program.slot, started_at=started, status="running")
        shared = dict(context or {})
        shared.setdefault("program_id", program.program_id)
        shared.setdefault("question", program.question)

        evidence_agents = tuple(agent for agent in program.agent_specs if agent.role not in {"reconciler", "evaluator"})
        final_agents = tuple(agent for agent in program.agent_specs if agent.role in {"reconciler", "evaluator"})
        evidence_results = await self._run_parallel_phase(program, evidence_agents, shared)
        result.agent_results.extend(evidence_results)
        result.findings.extend(finding for row in evidence_results for finding in row.findings)
        result.follow_up_questions.extend(question for row in evidence_results for question in row.follow_up_questions)

        synthesis_context = dict(shared)
        synthesis_context["evidence_results"] = [asdict(row) for row in evidence_results]
        final_results = await self._run_parallel_phase(program, final_agents, synthesis_context)
        result.agent_results.extend(final_results)
        result.findings.extend(finding for row in final_results for finding in row.findings)
        result.follow_up_questions.extend(question for row in final_results for question in row.follow_up_questions)

        result.completed_at = datetime.now(timezone.utc)
        if all(row.status == "completed" for row in result.agent_results):
            result.status = "completed"
        elif any(row.status == "completed" for row in result.agent_results):
            result.status = "partial"
        elif any(row.status == "blocked" for row in result.agent_results):
            result.status = "blocked"
        else:
            result.status = "failed"
        return result

    async def run_programs(self, programs: tuple[ResearchProgram, ...], *, context: dict[str, object] | None = None) -> list[ProgramResult]:
        if not programs:
            return []
        return list(await asyncio.gather(*(self.run_program(program, context=context) for program in programs)))


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
