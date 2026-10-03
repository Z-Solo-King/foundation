import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).parents[1]
SHA_RE = re.compile(r"^[0-9a-f]{40}$")


def test_family_sync_state_matches_current_main_and_graph():
    state = json.loads((ROOT / "docs/FAMILY_SYNC_STATE.json").read_text(encoding="utf-8"))
    graph = json.loads((ROOT / "docs/FAMILY_INTEGRATION_GRAPH.json").read_text(encoding="utf-8"))
    assert state["schema_version"] == "family-sync-state/v1"
    assert state["status"] == "CURRENT"
    assert state["head_reference_mode"] == "live_github"
    assert SHA_RE.fullmatch(state["live_main"]["foundation"])
    assert SHA_RE.fullmatch(state["live_main"]["operations"])
    assert SHA_RE.fullmatch(state["last_verified_main"]["foundation"])
    assert SHA_RE.fullmatch(state["last_verified_main"]["operations"])
    queue = state["current_queue"]
    assert queue["schema"] == "live-issue-snapshot/v1"
    assert queue["open_issue_count"] == len(queue["foundation"]) + queue["operations_count"]
    assert queue["operations_count"] == len(queue.get("operations", []))
    assert queue["operations_issue_numbers_omitted"] is False
    assert set(queue["foundation"]).issuperset({58, 157, 1249})
    assert 603 in queue["operations"]
    assert graph["schema"] == "family-integration-graph/v1"
    assert len(graph["material_registry"]) == 20
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    assert SHA_RE.fullmatch(head)
