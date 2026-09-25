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
    assert state["current_queue"]["open_issue_count"] == 10
    assert state["current_queue"]["foundation"] == [58, 1157, 157]
    assert state["current_queue"]["operations"] == [145, 197, 340, 385, 597, 603, 699]
    assert state["current_integration"]["graph_schema"] == "family-integration-graph/v1"
    assert state["current_integration"]["graph_blob_sha"]
    assert state["current_integration"]["material_count"] == 20
    assert state["current_integration"]["benchmark_probe_count"] == 10
    assert graph["schema"] == "family-integration-graph/v1"
    assert len(graph["material_registry"]) == 20
