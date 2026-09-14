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
    agent_budget_hint: int = 6

    def __post_init__(self) -> None:
        if self.lane not in {0, 1, 2}:
            raise ValueError("lane must be 0, 1 or 2")
        if not 0 <= self.slot < 8:
            raise ValueError("slot must be between 0 and 7")
        if not self.program_id.strip() or not self.title.strip() or not self.question.strip():
            raise ValueError("program_id, title and question are required")
        if not 1 <= len(self.agent_specs) <= 10:
            raise ValueError("each program must contain 1-10 logical agents")
        if not 1 <= self.agent_budget_hint <= len(self.agent_specs):
            raise ValueError("agent_budget_hint must be within the agent count")

    @property
    def max_active_agents(self) -> int:
        """Backward-compatible name for the program's initial budget hint.

        The scheduler does not use this as a hard concurrency limit; the global
        scheduler budget and the per-program agent_budget_hint determine allocation.
        """
        return self.agent_budget_hint


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

    @property
    def duration_seconds(self) -> float:
        return max(0.0, (self.completed_at - self.started_at).total_seconds())


@dataclass
class ProgramResult:
    program_id: str
    lane: int
    slot: int
    started_at: datetime
    completed_at: datetime | None = None
    status: Literal["planned", "running", "completed", "partial", "blocked", "failed"] = "planned"
    allocated_agents: int = 0
    agent_results: list[AgentResult] = field(default_factory=list)
    findings: list[dict[str, object]] = field(default_factory=list)
    follow_up_questions: list[str] = field(default_factory=list)

    @property
    def completed_agents(self) -> int:
        return sum(row.status == "completed" for row in self.agent_results)

    @property
    def failed_agents(self) -> int:
        return sum(row.status == "failed" for row in self.agent_results)

    @property
    def wall_clock_seconds(self) -> float:
        end = self.completed_at or datetime.now(timezone.utc)
        return max(0.0, (end - self.started_at).total_seconds())

    @property
    def agent_seconds(self) -> float:
        return sum(row.duration_seconds for row in self.agent_results)

    @property
    def unique_source_count(self) -> int:
        sources: set[str] = set()
        for finding in self.findings:
            source = finding.get("source_url") or finding.get("url")
            if isinstance(source, str) and source:
                sources.add(source)
        return len(sources)

    @property
    def useful_finding_count(self) -> int:
        return sum(1 for finding in self.findings if any(value not in (None, "", [], {}) for value in finding.values()))

    @property
    def duplicate_rate(self) -> float:
        if not self.findings:
            return 0.0
        signatures = {(str(row.get("claim", "")), str(row.get("source_url", row.get("url", "")))) for row in self.findings}
        return max(0.0, 1.0 - (len(signatures) / len(self.findings)))

    @property
    def answer_quality(self) -> float | None:
        scores: list[float] = []
        for finding in self.findings:
            value = finding.get("answer_quality")
            if isinstance(value, (int, float)):
                scores.append(max(0.0, min(10.0, float(value))))
        return round(sum(scores) / len(scores), 3) if scores else None

    def measurement(self) -> dict[str, object]:
        return {
            "allocated_agents": self.allocated_agents,
            "completed_agents": self.completed_agents,
            "failed_agents": self.failed_agents,
            "wall_clock_seconds": round(self.wall_clock_seconds, 3),
            "agent_seconds": round(self.agent_seconds, 3),
            "useful_findings": self.useful_finding_count,
            "unique_sources": self.unique_source_count,
            "duplicate_rate": round(self.duplicate_rate, 4),
            "answer_quality_0_to_10": self.answer_quality,
            "follow_up_questions": len(self.follow_up_questions),
        }


@dataclass(frozen=True)
class CapacityComparison:
    program_id: str
    low: ProgramResult
    high: ProgramResult

    def to_dict(self) -> dict[str, object]:
        low = self.low.measurement()
        high = self.high.measurement()
        low_quality = low["answer_quality_0_to_10"]
        high_quality = high["answer_quality_0_to_10"]
        return {
            "program_id": self.program_id,
            "low": low,
            "high": high,
            "delta_wall_clock_seconds": round(float(high["wall_clock_seconds"]) - float(low["wall_clock_seconds"]), 3),
            "delta_agent_seconds": round(float(high["agent_seconds"]) - float(low["agent_seconds"]), 3),
            "delta_useful_findings": int(high["useful_findings"]) - int(low["useful_findings"]),
            "delta_unique_sources": int(high["unique_sources"]) - int(low["unique_sources"]),
            "delta_duplicate_rate": round(float(high["duplicate_rate"]) - float(low["duplicate_rate"]), 4),
            "delta_answer_quality_0_to_10": None if low_quality is None or high_quality is None else round(float(high_quality) - float(low_quality), 3),
        }
