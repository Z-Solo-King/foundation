from pathlib import Path

WORKFLOW = Path(__file__).parents[1] / ".github" / "workflows" / "nightly-multi-agent-research-v3.yml"


def test_nightly_workflow_uses_pinned_private_operations_matrix():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "OPERATIONS_REPOSITORY: Z-Solo-King/operations" in text
    assert "OPERATIONS_RESEARCH_REF: cfcc3b4801d62d62c9133ba3402ae14ea253eedf" in text
    assert "private.multi_agent.runner" in text
    assert "private.multi_agent.project_research" in text
    assert "nightly-lane-${{ matrix.lane }}" in text
    assert "lane: 0" in text and "lane: 1" in text and "lane: 2" in text