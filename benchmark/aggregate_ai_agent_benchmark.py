"""Aggregate project-native AI/agent benchmark observations using the existing scorer."""
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

from benchmark.ai_agent_benchmark_contract import validate_observation_envelope
from benchmark.agent_behavior_benchmark import load_observation, score_run


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            value = json.loads(line)
            if not isinstance(value, dict):
                raise ValueError(f"{path}:{line_number}: observation must be an object")
            rows.append(value)
    return rows


def aggregate(rows: list[dict[str, Any]]) -> dict[str, Any]:
    if not rows:
        raise ValueError("no benchmark observations supplied")

    scores = []
    by_role: dict[str, list[float]] = defaultdict(list)
    by_lane: dict[str, list[float]] = defaultdict(list)

    for row in rows:
        errors = validate_observation_envelope(row)
        if errors:
            raise ValueError("; ".join(errors))
        score = score_run(load_observation(row["observation"]))
        scores.append(score)
        by_role[row["agent_role"]].append(score.overall)
        by_lane[row["lane"]].append(score.overall)

    models: dict[str, list[float]] = defaultdict(list)
    for score in scores:
        models[score.model].append(score.overall)

    return {
        "schema": "heroic-ai-agent-benchmark-report/v1",
        "observations": len(scores),
        "models": {
            model: {
                "runs": len(values),
                "mean_overall": round(sum(values) / len(values), 3),
            }
            for model, values in sorted(models.items())
        },
        "roles": {
            role: {
                "runs": len(values),
                "mean_overall": round(sum(values) / len(values), 3),
            }
            for role, values in sorted(by_role.items())
        },
        "lanes": {
            lane: {
                "runs": len(values),
                "mean_overall": round(sum(values) / len(values), 3),
            }
            for lane, values in sorted(by_lane.items())
        },
        "scores": [score.to_dict() for score in scores],
        "hard_gate_rule": "numeric observations never override security/policy/provenance/runtime/production gates",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Aggregate AI/agent benchmark observation envelopes.")
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    report = aggregate(_read_jsonl(args.input))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": "PASS",
        "observations": report["observations"],
        "models": sorted(report["models"]),
        "roles": sorted(report["roles"]),
        "lanes": sorted(report["lanes"]),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
