from pathlib import Path

WORKFLOW = Path(__file__).parents[1] / ".github" / "workflows" / "nightly-multi-agent-research-v3.yml"

def test_nightly_workflow_uses_pinned_private_operations_crossfire_runner():
    text=WORKFLOW.read_text(encoding="utf-8")
    research=text.split("  research:",1)[1].split("\n  migration_review:",1)[0]
    assert "OPERATIONS_REPOSITORY: Z-Solo-King/operations" in text
    assert "OPERATIONS_RESEARCH_REF:" in text
    assert "6e1b18ab6b8460c63f5cf664d6915f0a9bc71293" in text
    assert "private.multi_agent.runner" in research
    assert "--crossfire" in research
    assert "--global-capacity 20" in research
    assert "matrix:" not in research
    assert "production_release_run_id" in text

def test_crossfire_preserves_three_lane_8_program_contract():
    text=WORKFLOW.read_text(encoding="utf-8")
    assert text.count("name: Upload nightly research lane 0")==1
    assert text.count("name: Upload nightly research lane 1")==1
    assert text.count("name: Upload nightly research lane 2")==1
    assert "expected={f'lane{lane}-slot{slot}' for slot in range(8)}" in text