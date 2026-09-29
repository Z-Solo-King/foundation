import json
from pathlib import Path


ROOT = Path(__file__).parents[1]


def test_family_sync_state_matches_current_main_and_graph():
    state = json.loads((ROOT / "docs" / "FAMILY_SYNC_STATE.json").read_text(encoding="utf-8"))
    graph = json.loads((ROOT / "docs" / "FAMILY_INTEGRATION_GRAPH.json").read_text(encoding="utf-8"))
    assert state["schema_version"] == "family-sync-state/v1"
    assert state["status"] == "CURRENT"
    assert state["live_main"]["foundation"]
    assert state["live_main"]["operations"]
    queue = state["current_queue"]
    assert queue["schema"] == "live-issue-snapshot/v1"
    assert queue["open_issue_count"] == len(queue["foundation"]) + queue["operations_count"]
    assert queue["foundation"] == [58, 1157, 157, 1247, 1249]
    assert queue["operations_count"] == 8
    assert queue["operations_issue_numbers_omitted"] is True
    assert graph["schema"] == "family-integration-graph/v1"
    assert len(graph["material_registry"]) == 20
