"""Validate the audit-derived AI/agent benchmark contract."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def main() -> int:
    matrix = json.loads((ROOT / "ai_agent_task_matrix_2026-09-25.json").read_text(encoding="utf-8"))
    schema = json.loads((ROOT / "ai_agent_observation.schema.json").read_text(encoding="utf-8"))
    assert matrix["schema"] == "heroic-ai-agent-benchmark-matrix/v1"
    assert matrix["repetitions_per_task_model"] == 3
    assert matrix["roles"] == ["main", "explorer", "worker", "researcher", "advisor"]
    assert list(matrix["lanes"]) == ["L1", "L2", "L3", "L4", "L5", "L6"]
    assert schema["properties"]["schema"]["const"] == "heroic-ai-agent-benchmark-observation/v1"
    task_ids = [task["id"] for task in matrix["tasks"]]
    assert len(task_ids) == len(set(task_ids))
    assert len(task_ids) >= 24
    for task in matrix["tasks"]:
        assert task["lane"] in matrix["lanes"]
        assert task["roles"]
        assert set(task["roles"]).issubset(matrix["roles"])
    print(json.dumps({
        "status": "PASS",
        "lanes": 6,
        "roles": len(matrix["roles"]),
        "tasks": len(task_ids),
        "repetitions_per_task_model": 3
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
