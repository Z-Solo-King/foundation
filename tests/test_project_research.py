from __future__ import annotations

from pathlib import Path

from benchmark.multi_agent.models import AgentResult, ProgramResult
from benchmark.multi_agent.project_research import build_summary, collect_project_snapshot
from datetime import datetime, timezone


def _result(*, findings=None, status="completed") -> ProgramResult:
    now = datetime.now(timezone.utc)
    return ProgramResult(
        program_id="lane1-slot0",
        lane=1,
        slot=0,
        started_at=now,
        completed_at=now,
        status=status,
        allocated_agents=1,
        agent_results=[AgentResult.now("agent", "completed")],
        findings=list(findings or []),
    )


def test_project_snapshot_is_revision_anchored() -> None:
    snapshot = collect_project_snapshot(Path("."))
    assert snapshot["revision"]
    assert isinstance(snapshot["tracked_file_count"], int)
    assert set(snapshot["key_paths"]) == {"benchmark", "tests", "workflows", "docs"}


def test_external_findings_are_candidate_only_without_receipt(tmp_path: Path) -> None:
    result = _result(findings=[{"claim": "possible improvement", "source_url": "https://example.com"}])
    summary = build_summary([result], tmp_path)
    finding = summary["programs"][0]["findings"][0]
    assert finding["evidence_status"] == "candidate_unverified"
    assert finding["accepted_as_project_evidence"] is False


def test_zero_evidence_creates_improvement_signal(tmp_path: Path) -> None:
    summary = build_summary([_result()], tmp_path)
    signals = summary["improvement_signals"]
    assert any(signal["type"] == "evidence_gap" for signal in signals)


def test_failed_program_sets_partial_execution_state(tmp_path: Path) -> None:
    summary = build_summary([_result(status="failed")], tmp_path)
    assert summary["execution_state"] == "partial_or_failed"
