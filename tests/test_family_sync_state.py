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
    assert state["current_queue"]["open_issue_count"] == len(state["current_queue"]["foundation"]) + state["current_queue"]["operations_count"]
    assert state["current_queue"]["foundation"] == [1370, 1249, 1247, 1157, 157, 58]
    assert state["current_queue"]["operations_count"] == 6
    assert graph["schema"] == "family-integration-graph/v1"
    assert len(graph["material_registry"]) == 20
