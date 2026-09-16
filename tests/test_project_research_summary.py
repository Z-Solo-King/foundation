from pathlib import Path

from benchmark.multi_agent.models import AgentResult, ProgramResult
from benchmark.multi_agent.project_research import build_summary
from datetime import datetime, timezone


def _program(program_id: str, *, useful: int, sources: int, followups: int = 0, status: str = "completed"):
    now = datetime.now(timezone.utc)
    finding = {
        "claim": "candidate finding",
        "source_url": "https://example.com/source" if sources else None,
        "source_family": "github" if sources else None,
        "acquisition_method": "direct" if sources else None,
    }
    return ProgramResult(
        program_id=program_id,
        lane=0,
        slot=0,
        started_at=now,
        completed_at=now,
        status=status,
        allocated_agents=1,
        agent_results=(
            AgentResult(
                agent_id="agent-1",
                status="completed",
                started_at=now,
                completed_at=now,
                findings=(finding,) if useful else (),
                follow_up_questions=tuple(f"q-{i}" for i in range(followups)),
                note="",
            ),
        ),
        findings=[finding] if useful else [],
        follow_up_questions=[f"q-{i}" for i in range(followups)],
    )


def test_summary_exposes_candidate_and_follow_up_metrics(tmp_path: Path):
    summary = build_summary(
        [_program("lane0-slot0", useful=1, sources=1, followups=2)],
        tmp_path,
        run_id="123",
    )
    assert summary["schema"] == "project-improvement-research/v1"
    assert summary["metrics"]["programs_completed"] == 1
    assert summary["metrics"]["findings"] == 1
    assert summary["metrics"]["candidate_unverified_findings"] == 1
    assert summary["metrics"]["follow_up_questions"] == 2
    assert any(signal["type"] == "follow_up_backlog" for signal in summary["improvement_signals"])
