from pathlib import Path


ROOT = Path(__file__).parents[1] / ".github" / "workflows"


def test_fresh_nightly_identity_is_dispatchable_and_uses_current_operations():
    text = (ROOT / "nightly-multi-agent-research-v2.yml").read_text(encoding="utf-8")
    assert "workflow_dispatch:" in text
    assert "schedule:" in text
    assert "OPERATIONS_REPOSITORY: Z-Solo-King/operations" in text
    assert "OPERATIONS_RESEARCH_REF: 41db817dee6aa7d369ea9a07dd072b58ece1695a" in text
    assert "private.multi_agent.runner" in text
    assert "private.multi_agent.project_research" in text


def test_fresh_bridge_identity_is_dispatchable_and_bounded():
    text = (ROOT / "foundation-canonical-workflow-bridge-v3.yml").read_text(encoding="utf-8")
    assert "workflow_dispatch:" in text
    assert "main-push-actions-control-plane-probe-v2.yml" in text
    assert "nightly-multi-agent-research-v2.yml" in text
    assert "workflow-dispatch-bridge-receipt/v2" in text
    assert "actions/upload-artifact@" in text


def test_fresh_acceptance_workflow_dispatches_both_identities():
    text = (ROOT / "fresh-control-plane-identity-acceptance.yml").read_text(encoding="utf-8")
    assert "gh workflow run foundation-canonical-workflow-bridge-v3.yml" in text
    assert "gh workflow run nightly-multi-agent-research-v2.yml" in text
    assert "jobs?per_page=100" in text