from __future__ import annotations

import argparse
import asyncio
import json
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path

from .llm import configured_executor
from .orchestrator import JsonlResearchReporter, MultiAgentCoordinator
from .programs import NIGHTLY_PROGRAMS


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run one isolated nightly research experiment for the 20-job matrix")
    parser.add_argument("--program-id", required=True)
    parser.add_argument("--agent-budget", type=int, choices=range(1, 11), default=6)
    parser.add_argument("--global-capacity", type=int, choices=range(1, 21), default=20)
    parser.add_argument("--focus", required=True)
    parser.add_argument("--tag", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


async def run(args: argparse.Namespace) -> None:
    matches = [program for program in NIGHTLY_PROGRAMS if program.program_id == args.program_id]
    if len(matches) != 1:
        raise SystemExit(f"unknown or non-unique program id: {args.program_id}")
    base = matches[0]
    experiment_id = f"{base.program_id}:{args.tag}"
    program = replace(base, program_id=experiment_id, title=f"{base.title} [{args.tag}]", question=args.focus)

    executor = None if args.dry_run else configured_executor()
    if executor is None and not args.dry_run:
        raise RuntimeError("Live research executor is not configured; refusing silent dry-run")

    coordinator = MultiAgentCoordinator(global_active_agents=args.global_capacity, executor=executor)
    context = {
        "night_date": datetime.now(timezone.utc).date().isoformat(),
        "mode": "dry-run" if args.dry_run else "llm",
        "experiment_tag": args.tag,
        "experiment_focus": args.focus,
        "agent_budget": args.agent_budget,
        "matrix_capacity": args.global_capacity,
        "must_cross_check": True,
        "must_report_failures": True,
        "must_not_claim_unobserved_tool_use": True,
    }
    result = await coordinator.run_program(program, context=context, agent_budget=args.agent_budget)
    reporter = JsonlResearchReporter(Path(args.output))
    reporter.append(result)
    print(json.dumps({"event": "matrix_experiment_completed", "tag": args.tag, "program_id": result.program_id, "status": result.status, "allocated_agents": result.allocated_agents, "measurement": result.measurement(), "mode": context["mode"]}, sort_keys=True))
    if result.status != "completed":
        raise RuntimeError(f"matrix experiment incomplete: {result.program_id} status={result.status}")


if __name__ == "__main__":
    asyncio.run(run(parse_args()))
