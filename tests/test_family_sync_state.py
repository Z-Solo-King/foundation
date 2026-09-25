import json
from pathlib import Path


ROOT = Path(__file__).parents[1]


def test_family_sync_state_matches_current_main_and_graph():
    state = json.loads((ROOT / "docs" / "FAMILY_SYNC_STATE.json").read_text(encoding="utf-8"))
    graph = json.loads((ROOT / "docs" / "FAMILY_INTEGRATION_GRAPH.json").read_text(encoding="utf-8"))
    assert state["schema_version"] == "family-sync-state/v1"
    assert state["status"] == "CURRENT"
    assert state["live_main"]["foundation"] == "6183a18a8f4373099264b3c193bc91402045d091"
    assert state["live_main"]["operations"] == "06c763aba521b0d7060b22e10ea8f195008a63a3"
    assert state["current_queue"]["open_issue_count"] == 11
    assert state["current_queue"]["foundation"] == [58, 1157, 154, 157]
    assert state["current_queue"]["operations"] == [145, 197, 340, 385, 597, 603, 699]
    assert state["current_integration"]["graph_schema"] == "family-integration-graph/v1"
    assert state["current_integration"]["graph_blob_sha"] == "6b86edcc2bb4ce72654837c76dd5835477c2d8d4"
    assert state["current_integration"]["material_count"] == 20
    assert state["current_integration"]["benchmark_probe_count"] == 11
    assert graph["schema"] == "family-integration-graph/v1"
    assert len(graph["material_registry"]) == 20
