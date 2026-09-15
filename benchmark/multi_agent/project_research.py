from __future__ import annotations

import argparse
import json
import os
import subprocess
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from .models import ProgramResult

SCHEMA = "project-improvement-research/v1"


def _git(root: Path, *args: str) -> str:
    try:
        return subprocess.check_output(["git", *args], cwd=root, text=True, stderr=subprocess.DEVNULL).strip()
    except (OSError, subprocess.CalledProcessError):
        return ""


def collect_project_snapshot(root: Path) -> dict[str, object]:
    root = root.resolve()
    revision = _git(root, "rev-parse", "HEAD")
    branch = _git(root, "rev-parse", "--abbrev-ref", "HEAD")
    commit_subject = _git(root, "log", "-1", "--pretty=%s")
    commit_time = _git(root, "show", "-s", "--format=%cI", "HEAD")
    status = _git(root, "status", "--porcelain")
    tracked = _git(root, "ls-files")
    files = [line for line in tracked.splitlines() if line]
    return {
        "repository": os.getenv("GITHUB_REPOSITORY", "local"),
        "revision": revision,
        "branch": branch,
        "commit_subject": commit_subject,
        "commit_time": commit_time,
        "working_tree_clean": not bool(status),
        "tracked_file_count": len(files),
        "key_paths": {
            "benchmark": sum(path.startswith("benchmark/") for path in files),
            "tests": sum(path.startswith("tests/") for path in files),
            "workflows": sum(path.startswith(".github/workflows/") for path in files),
            "docs": sum(path.startswith("docs/") for path in files),
        },
    }


def _finding(row: ProgramResult, finding: dict[str, object], snapshot: dict[str, object]) -> dict[str, object]:
    source_url = finding.get("source_url") or finding.get("url")
    return {
        "program_id": row.program_id,
        "lane": row.lane,
        "slot": row.slot,
        "status": row.status,
        "claim": finding.get("claim") or finding.get("finding") or finding.get("title") or "",
        "source_url": source_url if isinstance(source_url, str) else None,
        "source_family": finding.get("source_family"),
        "acquisition_method": finding.get("acquisition_method"),
        "evidence_status": "candidate_unverified" if source_url else "model_observation",
        "accepted_as_project_evidence": False,
        "revision": snapshot.get("revision"),
    }


def _program_record(row: ProgramResult, snapshot: dict[str, object]) -> dict[str, object]:
    findings = [_finding(row, finding, snapshot) for finding in row.findings]
    return {
        "program_id": row.program_id,
        "lane": row.lane,
        "slot": row.slot,
        "status": row.status,
        "measurement": row.measurement(),
        "findings": findings,
        "follow_up_questions": list(row.follow_up_questions),
        "agent_notes": [agent.note for agent in row.agent_results if agent.note],
    }


def _improvement_signals(programs: Iterable[dict[str, object]]) -> list[dict[str, object]]:
    programs = tuple(programs)
    by_program = {str(row["program_id"]): row for row in programs}
    signals: list[dict[str, object]] = []

    for program_id in sorted(by_program):
        row = by_program[program_id]
        measurement = row.get("measurement") or {}
        if not isinstance(measurement, dict):
            continue
        useful = int(measurement.get("useful_findings", 0) or 0)
        sources = int(measurement.get("unique_sources", 0) or 0)
        status = row.get("status")
        if status != "completed" or useful == 0:
            signals.append({
                "type": "evidence_gap",
                "program_id": program_id,
                "severity": "high" if status != "completed" else "medium",
                "reason": "program completed without usable evidence or did not complete",
                "decision": "ISSUE",
            })
        elif sources == 0:
            signals.append({
                "type": "source_provenance_gap",
                "program_id": program_id,
                "severity": "medium",
                "reason": "findings exist without source URLs; external claims remain unverified",
                "decision": "WATCH",
            })

    if any(str(row["program_id"]).startswith("lane1-slot") for row in programs):
        signals.append({
            "type": "acquisition_bridge",
            "program_id": "lane1",
            "severity": "high",
            "reason": "chatbot and mapper programs require a real acquisition/evidence path before their findings can become accepted evidence",
            "decision": "IMPLEMENT",
            "related_issue": "operations#79",
        })

    return signals


def build_summary(program_results: Iterable[ProgramResult], root: Path, *, run_id: str = "") -> dict[str, object]:
    snapshot = collect_project_snapshot(root)
    rows = [_program_record(row, snapshot) for row in program_results]
    status_counts = Counter(str(row["status"]) for row in rows)
    return {
        "schema": SCHEMA,
        "research_id": f"nightly-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}",
        "run_id": run_id,
        "research_mode": "project_improvement",
        "execution_state": "completed" if rows and all(row["status"] == "completed" for row in rows) else "partial_or_failed",
        "evidence_policy": {
            "repo_state": "accepted_direct_evidence",
            "llm_findings": "candidate_only_until_acquisition_receipt",
            "external_source_urls": "candidate_only_until_verified",
            "model_hypotheses": "never_accepted_as_fact",
        },
        "project_snapshot": snapshot,
        "program_count": len(rows),
        "status_counts": dict(status_counts),
        "programs": rows,
        "improvement_signals": _improvement_signals(rows),
        "next_action_rule": "Only IMPLEMENT items that pass deterministic tests, security/policy checks, and regression comparison against baseline.",
    }


def load_jsonl(paths: Iterable[Path]) -> list[ProgramResult]:
    from .models import AgentResult
    from datetime import datetime

    rows: list[ProgramResult] = []
    for path in paths:
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            payload = json.loads(line)
            if payload.get("schema") == "multi-agent-capacity/v1":
                continue
            agents = []
            for agent in payload.get("agent_results", []):
                agents.append(
                    AgentResult(
                        agent_id=str(agent["agent_id"]),
                        status=agent["status"],
                        started_at=datetime.fromisoformat(agent["started_at"]),
                        completed_at=datetime.fromisoformat(agent["completed_at"]),
                        findings=tuple(agent.get("findings", [])),
                        follow_up_questions=tuple(agent.get("follow_up_questions", [])),
                        note=str(agent.get("note", "")),
                    )
                )
            rows.append(
                ProgramResult(
                    program_id=str(payload["program_id"]),
                    lane=int(payload["lane"]),
                    slot=int(payload["slot"]),
                    started_at=datetime.fromisoformat(payload["started_at"]),
                    completed_at=datetime.fromisoformat(payload["completed_at"]) if payload.get("completed_at") else None,
                    status=payload["status"],
                    allocated_agents=int(payload.get("allocated_agents", 0)),
                    agent_results=agents,
                    findings=list(payload.get("findings", [])),
                    follow_up_questions=list(payload.get("follow_up_questions", [])),
                )
            )
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description="Build an auditable nightly project-improvement research summary")
    parser.add_argument("--root", default=".")
    parser.add_argument("--input", nargs="+", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--run-id", default="")
    args = parser.parse_args()
    summary = build_summary(load_jsonl(tuple(Path(value) for value in args.input)), Path(args.root), run_id=args.run_id)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "event": "project_research_summary",
        "schema": SCHEMA,
        "research_id": summary["research_id"],
        "revision": summary["project_snapshot"]["revision"],
        "program_count": summary["program_count"],
        "improvement_signals": len(summary["improvement_signals"]),
        "execution_state": summary["execution_state"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
