from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_open_issue_acceptance_matrix_is_current_and_complete() -> None:
    matrix = json.loads(
        (ROOT / "docs" / "OPEN_ISSUE_ACCEPTANCE_MATRIX.json").read_text(encoding="utf-8")
    )
    assert matrix["schema"] == "family-issue-acceptance-matrix/v1"
    assert matrix["open_issue_count"] == 21
    issues = {(row["repo"], row["number"]) for row in matrix["issues"]}
    assert issues == {
        ("foundation", 58),
        ("foundation", 1157),
        ("foundation", 157),
        ("foundation", 1247),
        ("foundation", 1249),
        ("foundation", 1265),
        ("foundation", 1281),
        ("foundation", 1283),
        ("foundation", 1284),
        ("operations", 145),
                ("operations", 340),
        ("operations", 385),
        ("operations", 597),
        ("operations", 603),
        ("operations", 699),
        ("operations", 713),
        ("operations", 994),
        ("operations", 997),
        ("operations", 998),
        ("operations", 1005),
    }
    assert matrix["graph_reference"]["schema"] == "family-integration-graph/v1"
    assert matrix["graph_reference"]["materials"] == 20
    assert matrix["graph_reference"]["probes"] == 11


def test_benchmark_matrix_has_no_closed_issue_282_targets() -> None:
    tasks = json.loads(
        (ROOT / "benchmark" / "ai_agent_task_matrix_v1.json").read_text(encoding="utf-8")
    )["tasks"]
    assert all("Foundation #282" not in str(task.get("project_surface")) for task in tasks)
