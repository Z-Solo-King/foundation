from pathlib import Path


WORKFLOW = Path(__file__).parents[1] / ".github" / "workflows" / "nightly-multi-agent-research.yml"


def workflow_text() -> str:
    return WORKFLOW.read_text(encoding="utf-8")


def test_matrix_is_fail_fast_false_and_has_three_lanes():
    text = workflow_text()
    assert "fail-fast: false" in text
    assert "lane: 0" in text
    assert "lane: 1" in text
    assert "lane: 2" in text


def test_lane_status_and_artifact_steps_are_always_run():
    text = workflow_text()
    assert "name: Materialize truthful lane status" in text
    assert "if: ${{ always() }}" in text
    assert "name: nightly-research-lane-${{ matrix.lane }}" in text
    assert "-status.json" in text


def test_summary_is_always_run_and_final_gate_preserves_failure():
    text = workflow_text()
    assert "name: Diagnose nightly Heroic AI research" in text
    assert "needs: research" in text
    assert "if: ${{ always() }}" in text
    assert "name: Preserve truthful nightly result" in text
    assert "needs: [research, project-summary]" in text
    assert "One or more research lanes failed/blocked" in text


def test_scheduled_workflow_never_requests_dry_run_implicitly():
    text = workflow_text()
    assert 'description: "Explicit deterministic dry-run for manual testing only"' in text
    assert "type: boolean" in text
    assert "args+=(--dry-run)" in text
    assert "if: ${{ steps.mode.outputs.mode == 'live' }}" in text


def test_incomplete_runs_do_not_build_project_improvement_summary():
    text = workflow_text()
    guard = "if: ${{ needs.research.result == 'success' && inputs.dry_run != true }}"
    assert text.count(guard) >= 7
    assert "real_research_findings_allowed" in text
    assert "historical_dry_run_findings_are_real_research': False" in text
