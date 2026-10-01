from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "provider-fleet-runtime-state.yml"


def test_provider_fleet_task_workflow_is_paused():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "workflow_dispatch:" in text
    assert "\nschedule:" not in text
    assert "\npush:" not in text
    assert "task workflow is paused" in text
    assert "jobs:" in text
    assert "  paused:" in text
    assert "provider-probe" not in text
    assert "CLOUDFLARE_API_TOKEN" not in text
    assert "PROVIDER_KEYS_JSON" not in text
