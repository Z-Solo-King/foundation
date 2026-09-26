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
    assert state["current_queue"]["open_issue_count"] == 11
    assert state["current_queue"]["foundation"] == [58, 157, 1157, 1247, 1249, 1305, 1306]
    assert state["current_queue"]["operations_count"] == 4
        assert graph["schema"] == "family-integration-graph/v1"
    assert len(graph["material_registry"]) == 20
