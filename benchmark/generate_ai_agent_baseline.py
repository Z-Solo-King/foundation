#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path
from typing import Any

from ai_agent_benchmark_contract import validate_manifest

def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def build_baseline(manifest: dict[str, Any], matrix_path: Path) -> dict[str, Any]:
    errors = validate_manifest(manifest)
    if errors:
        raise ValueError(json.dumps(errors))
    lanes = {x["code"]: x for x in manifest["lanes"]}
    tasks = manifest["tasks"]
    roles = sorted({role for task in tasks for role in task["agent_roles"]})
    return {
        "schema": "ai-agent-benchmark-baseline/v1",
        "execution_status": "structural_contract_only",
        "provider_backed_execution": False,
        "note": "Contract/baseline metadata only. It is not a model performance result and does not certify runtime behavior.",
        "matrix_digest": digest(matrix_path),
        "task_count": len(tasks),
        "lane_count": len(lanes),
        "repeat_count": 3,
        "agent_roles": roles,
        "tasks_by_lane": {code: sum(1 for t in tasks if t["lane"] == code) for code in lanes},
        "scoring_dimensions": manifest["scoring_dimensions"],
        "hard_gates": manifest["hard_gates"],
        "current_issue_targets": manifest["current_issue_targets"],
        "provenance_fields": manifest["provenance_fields"],
        "execution_recipe": {
            "per_task_repeats": 3,
            "preserve_each_observation": True,
            "same_tool_policy": True,
            "same_fixture_revision": True,
            "compare_outcomes_not_personality": True,
            "runtime_evidence_separate": True,
        },
    }

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--matrix", type=Path, default=Path("benchmark/ai_agent_task_matrix_v1.json"))
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    manifest = json.loads(args.matrix.read_text(encoding="utf-8"))
    baseline = build_baseline(manifest, args.matrix)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(baseline, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(baseline, indent=2, sort_keys=True))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
