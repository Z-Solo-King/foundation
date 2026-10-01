from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "provider-fleet-runtime-state.yml"

def test_provider_fleet_task_workflow_is_paused():
    payload = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))
    assert payload["on"] == {"workflow_dispatch": None}
    assert "paused" in payload["jobs"]
    assert "task workflow is paused" in WORKFLOW.read_text(encoding="utf-8")
    assert "schedule" not in payload
