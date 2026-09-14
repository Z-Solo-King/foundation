from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Literal

AgentStatus = Literal["queued", "running", "completed", "blocked", "failed", "skipped"]


@dataclass(frozen=True)
class AgentSpec:
    agent_id: str
    role: str
    objective: str
    source_families: tuple[str, ...] = ()
    priority: int = 50


@dataclass(frozen=True)
class ResearchProgram:
    program_id: str
    lane: int
    slot: int
    category: str
    title: str
    question: str
    agent_specs: tuple[AgentSpec, ...]
    max_active_agents: int = 6

    def __post_init__(self) -> None:
        if self.lane not in {0, 1, 2}:
            raise ValueError("lane must be 0, 1 or 2")
        if not 0 <= self.slot < 8:
            raise ValueError("slot must be between 0 and 7")
        if not self.program_id.strip() or not self.title.strip() or not self.question.strip():
            raise ValueError("program_id, title and question are required")
        if not self.agent_specs or len(self.agent_specs) > 10:
            raise ValueError("each program must contain 1-10 logical agents")
        if not 1 <= self.max_active_agents <= len(self.agent_specs):
            raise ValueError("max_active_agents must be within the agent count")


@dataclass(frozen=True)
class AgentResult:
    agent_id: str
    status: AgentStatus
    started_at: datetime
    completed_at: datetime
    findings: tuple[dict[str, object], ...] = ()
    follow_up_questions: tuple[str, ...] = ()
    note: str = ""

    @classmethod
    def now(cls, agent_id: str, status: AgentStatus, note: str = "") -> "AgentResult":
        current = datetime.now(timezone.utc)
        return cls(agent_id=agent_id, status=status, started_at=current, completed_at=current, note=note)


@dataclass
class ProgramResult:
    program_id: str
    lane: int
    slot: int
    started_at: datetime
    completed_at: datetime | None = None
    status: Literal["planned", "running", "completed", "partial", "blocked", "failed"] = "planned"
    agent_results: list[AgentResult] = field(default_factory=list)
    findings: list[dict[str, object]] = field(default_factory=list)
    follow_up_questions: list[str] = field(default_factory=list)

    @property
    def completed_agents(self) -> int:
        return sum(row.status == "completed" for row in self.agent_results)

    @property
    def failed_agents(self) -> int:
        return sum(row.status == "failed" for row in self.agent_results)
