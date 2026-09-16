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


def test_private_operations_revision_and_app_auth_are_explicit():
    text = workflow_text()
    assert "OPERATIONS_REPOSITORY: Z-Solo-King/operations" in text
    assert "OPERATIONS_RESEARCH_REF: 48ef452e3be16d6117cc42b1968a1094de4974f4" in text
    assert "OPERATIONS_APP_ID: ${{ secrets.OPERATIONS_APP_ID }}" in text
    assert "OPERATIONS_APP_INSTALLATION_ID: ${{ secrets.OPERATIONS_APP_INSTALLATION_ID }}" in text
    assert "OPERATIONS_APP_PRIVATE_KEY: ${{ secrets.OPERATIONS_APP_PRIVATE_KEY }}" in text
    assert "private research source access: PASS" in text
    assert "private.multi_agent.runner" in text
    assert "private.multi_agent.project_research" in text
    assert "OPERATIONS_READ_TOKEN" not in text


def test_private_source_is_not_uploaded_as_an_artifact():
    text = workflow_text()
    assert "actions/upload-artifact" in text
    assert "operations-research" in text
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("path:") and not stripped.endswith("|"):
            assert "operations-research" not in stripped
    assert "Remove private research checkout and credentials" in text
    assert "Remove private project-research checkout and credentials" in text


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
