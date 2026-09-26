import json
from pathlib import Path

from benchmark.ai_agent_benchmark_contract import validate_manifest
from benchmark.generate_ai_agent_baseline import build_baseline

def test_manifest_is_valid_and_targets_current_open_queue():
    matrix = json.loads(Path("benchmark/ai_agent_task_matrix_v1.json").read_text())
    assert validate_manifest(matrix) == []
    assert matrix["current_issue_targets"] == {
        "foundation": [58, 157, 1157, 1247, 1249, 1265],
        "operations": [145, 597, 603, 699, 713, 997, 1005],
    }

def test_baseline_is_structural_only():
    path = Path("benchmark/ai_agent_task_matrix_v1.json")
    baseline = build_baseline(json.loads(path.read_text()), path)
    assert baseline["execution_status"] == "structural_contract_only"
    assert baseline["provider_backed_execution"] is False
    assert baseline["task_count"] == 24
    assert baseline["lane_count"] == 6
    assert baseline["repeat_count"] == 3
    assert sum(baseline["tasks_by_lane"].values()) == 24
