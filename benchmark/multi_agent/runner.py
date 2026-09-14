from __future__ import annotations

import argparse
import asyncio
import json
from datetime import datetime, timezone
from pathlib import Path

from .orchestrator import JsonlResearchReporter, MultiAgentCoordinator
from .programs import PROGRAMS_BY_LANE


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run one bounded slice of the nightly multi-agent research matrix")
    parser.add_argument("--lane", type=int, choices=(0, 1, 2), required=True)
    parser.add_argument("--start-slot", type=int, choices=range(8), required=True)
    parser.add_argument("--slots", type=int, choices=range(1, 5), default=4)
    parser.add_argument("--output", default=".runtime/multi-agent/research.jsonl")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--max-active-agents", type=int, default=18)
    return parser.parse_args()


async def run(args: argparse.Namespace) -> None:
    programs = PROGRAMS_BY_LANE[args.lane]
    end_slot = min(args.start_slot + args.slots, len(programs))
    selected = programs[args.start_slot:end_slot]
    reporter = JsonlResearchReporter(Path(args.output))
    coordinator = MultiAgentCoordinator(global_active_agents=args.max_active_agents)

    for program in selected:
        started = datetime.now(timezone.utc)
        print(json.dumps({
            "event": "program_started",
            "program_id": program.program_id,
            "lane": program.lane,
            "slot": program.slot,
            "started_at": started.isoformat(),
            "logical_agents": len(program.agent_specs),
            "max_active_agents": program.max_active_agents,
            "dry_run": args.dry_run,
        }))
        result = await coordinator.run_program(
            program,
            context={
                "night_date": started.date().isoformat(),
                "lane": args.lane,
                "slot": program.slot,
                "dry_run": args.dry_run,
            },
        )
        reporter.append(result)
        print(json.dumps({
            "event": "program_completed",
            "program_id": program.program_id,
            "status": result.status,
            "completed_agents": result.completed_agents,
            "failed_agents": result.failed_agents,
            "follow_up_questions": len(result.follow_up_questions),
        }))


def main() -> int:
    args = parse_args()
    asyncio.run(run(args))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
