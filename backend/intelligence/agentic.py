from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Literal

from .contracts import ResearchContract, ResearchPlan
from .evidence import EvidenceKnowledgeStore, EvidenceRecord
from .planning import create_plan

TaskStatus = Literal["pending", "running", "completed", "blocked", "failed", "skipped"]


@dataclass(frozen=True)
class ResearchTask:
    task_id: str
    objective: str
    stage: str
    status: TaskStatus = "pending"
    source_family: str | None = None
    parent_task_id: str | None = None
    reason: str = ""


@dataclass(frozen=True)
class TaskObservation:
    task_id: str
    status: Literal["completed", "blocked", "failed"]
    evidence: tuple[EvidenceRecord, ...] = field(default_factory=tuple)
    follow_up: tuple[ResearchTask, ...] = field(default_factory=tuple)
    note: str = ""


@dataclass(frozen=True)
class AgentState:
    question: str
    plan: ResearchPlan
    tasks: tuple[ResearchTask, ...]
    completed: tuple[str, ...] = field(default_factory=tuple)
    failed: tuple[str, ...] = field(default_factory=tuple)
    iterations: int = 0
    status: Literal["running", "completed", "blocked"] = "running"


class ResearchAgent:
    """Bounded planner-executor-evaluator loop with durable evidence storage.

    The controller intentionally does not perform network I/O. Adapters supply observations.
    This keeps policy, credentials, rate limits and acquisition implementation outside the
    control loop while still allowing autonomous follow-up task generation.
    """

    def __init__(
        self,
        evidence: EvidenceKnowledgeStore | None = None,
        executor: Callable[[ResearchTask, EvidenceKnowledgeStore], TaskObservation] | None = None,
        max_iterations: int = 32,
    ) -> None:
        if max_iterations < 1:
            raise ValueError("max_iterations must be positive")
        self.evidence = evidence or EvidenceKnowledgeStore()
        self.executor = executor
        self.max_iterations = max_iterations

    def create_state(self, contract: ResearchContract) -> AgentState:
        plan = create_plan(contract)
        tasks = tuple(
            ResearchTask(task_id=f"task-{index:03d}", objective=stage.replace("_", " "), stage=stage)
            for index, stage in enumerate(plan.stages, start=1)
        )
        return AgentState(question=contract.question, plan=plan, tasks=tasks)

    def step(self, state: AgentState) -> AgentState:
        if state.status != "running":
            return state
        if state.iterations >= self.max_iterations:
            return AgentState(**{**state.__dict__, "status": "blocked"})

        pending = next((task for task in state.tasks if task.status == "pending"), None)
        if pending is None:
            final_status = "blocked" if state.failed else "completed"
            return AgentState(**{**state.__dict__, "status": final_status})
        if self.executor is None:
            return AgentState(**{**state.__dict__, "iterations": state.iterations + 1, "status": "blocked"})

        running = ResearchTask(**{**pending.__dict__, "status": "running"})
        remaining = tuple(running if task.task_id == pending.task_id else task for task in state.tasks)
        observation = self.executor(running, self.evidence)
        for record in observation.evidence:
            self.evidence.upsert(record)

        spawned = list(observation.follow_up)
        completed = list(state.completed)
        failed = list(state.failed)
        if observation.status == "completed":
            completed.append(running.task_id)
            terminal: TaskStatus = "completed"
        elif observation.status == "blocked":
            failed.append(running.task_id)
            terminal = "blocked"
        else:
            failed.append(running.task_id)
            terminal = "failed"

        updated = [
            ResearchTask(**{**task.__dict__, "status": terminal}) if task.task_id == running.task_id else task
            for task in remaining
        ]
        updated.extend(spawned)
        return AgentState(
            question=state.question,
            plan=state.plan,
            tasks=tuple(updated),
            completed=tuple(completed),
            failed=tuple(failed),
            iterations=state.iterations + 1,
            status="running",
        )

    def run(self, state: AgentState) -> AgentState:
        current = state
        while current.status == "running" and current.iterations < self.max_iterations:
            current = self.step(current)
        if current.status == "running":
            current = AgentState(**{**current.__dict__, "status": "blocked"})
        return current


def research(request: str, executor: Callable[[ResearchTask, EvidenceKnowledgeStore], TaskObservation], depth: str = "standard") -> tuple[AgentState, EvidenceKnowledgeStore]:
    contract = ResearchContract(question=request, depth=depth)  # type: ignore[arg-type]
    agent = ResearchAgent(executor=executor)
    state = agent.run(agent.create_state(contract))
    return state, agent.evidence
