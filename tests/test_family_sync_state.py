import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).parents[1]


def test_family_sync_state_matches_current_main_and_graph():
    state = json.loads((ROOT / "docs" / "FAMILY_SYNC_STATE.json").read_text(encoding="utf-8"))
    graph = json.loads((ROOT / "docs" / "FAMILY_INTEGRATION_GRAPH.json").read_text(encoding="utf-8"))
    assert state["schema_version"] == "family-sync-state/v1"
    assert state["status"] == "CURRENT"
    assert state["head_reference_mode"] == "live_github"
    assert state["live_main"]["foundation"] == "READ_LIVE_FROM_GITHUB"
    assert state["live_main"]["operations"] == "READ_LIVE_FROM_GITHUB"
    assert len(state["last_verified_main"]["foundation"]) == 40
    assert len(state["last_verified_main"]["operations"]) == 40

    queue = state["current_queue"]
    assert queue["schema"] == "live-issue-snapshot/v1"
    assert queue["open_issue_count"] == len(queue["foundation"]) + queue["operations_count"]
    assert queue["foundation"] == [58, 1247, 1249, 157]
    assert queue["operations_count"] == len(queue.get("operations", []))
    assert queue["operations"] == [603]
    assert queue["total_open_issue_count"] == 5
    assert queue["operations_issue_numbers_omitted"] is False

    assert graph["schema"] == "family-integration-graph/v1"
    assert len(graph["material_registry"]) == 20
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    assert len(head) == 40
