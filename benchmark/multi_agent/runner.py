from __future__ import annotations

import argparse
import asyncio
import json
from datetime import datetime, timezone
from pathlib import Path

from .llm import configured_executor
from .orchestrator import CapacityExperiment, DynamicResearchScheduler, JsonlResearchReporter, MultiAgentCoordinator
from .programs import NIGHTLY_PROGRAMS


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run capacity-aware nightly multi-agent research")
    parser.add_argument("--start-slot", type=int, choices=range(8), default=0)
    parser.add_argument("--slots", type=int, choices=range(1, 9), default=8)
    parser.add_argument("--output", default=".runtime/multi-agent/research.jsonl")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--global-capacity", type=int, default=20)
    parser.add_argument("--compare", action="store_true", help="run a 5-vs-10 agent scaling comparison for two different research programs")
    return parser.parse_args()


async def run(args: argparse.Namespace) -> None:
    selected = tuple(program for program in NIGHTLY_PROGRAMS if args.start_slot <= program.slot < min(8, args.start_slot + args.slots))
    reporter = JsonlResearchReporter(Path(args.output))
    executor = None if args.dry_run else configured_executor()
    coordinator = MultiAgentCoordinator(global_active_agents=args.global_capacity, executor=executor)
    mode = "dry-run" if args.dry_run or executor is None else "llm"
    context = {"night_date": datetime.now(timezone.utc).date().isoformat(), "mode": mode}

    if args.compare:
        experiment = CapacityExperiment(coordinator)
        for program in selected[:2]:
            comparison = await experiment.compare(program, context=context)
            reporter.append(comparison.low)
            reporter.append(comparison.high)
            reporter.append_capacity_comparison(comparison)
            print(json.dumps({"event": "capacity_comparison", **comparison.to_dict()}))
        selected = selected[2:]

    scheduler = DynamicResearchScheduler(coordinator)
    print(json.dumps({
        "event": "research_window_started",
        "global_capacity": args.global_capacity,
        "programs": len(selected),
        "mode": mode,
    }))
    results = await scheduler.run(selected, context=context)
    for result in results:
        reporter.append(result)
        print(json.dumps({
            "event": "program_completed",
            "program_id": result.program_id,
            "allocated_agents": result.allocated_agents,
            "status": result.status,
            "measurement": result.measurement(),
            "mode": mode,
        }))


def main() -> int:
    asyncio.run(run(parse_args()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
