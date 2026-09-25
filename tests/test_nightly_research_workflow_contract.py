from pathlib import Path

WORKFLOW = Path(__file__).parents[1] / ".github" / "workflows" / "nightly-multi-agent-research-v3.yml"


def workflow_text() -> str:
    return WORKFLOW.read_text(encoding="utf-8")


def test_live_research_waits_for_exact_successful_production_release():
    text = workflow_text()
    assert "production_gate:" in text
    assert "heroic-ai-production-release.yml" in text
    assert 'target_sha="${GITHUB_SHA}"' in text
    assert "select(.headSha == $sha)" in text
    assert 'status == "completed" and .conclusion == "success"' in text
    assert "sleep 10" in text
    assert "needs: [production_gate]" in text
    assert 'Explicit dry-run: production release gate is not required.' in text

def test_matrix_is_fail_fast_false_and_has_three_lanes():
    text = workflow_text()
    assert "fail-fast: false" in text
    assert "lane: 0" in text
    assert "lane: 1" in text
    assert "lane: 2" in text


def test_private_operations_revision_and_app_auth_are_explicit():
    text = workflow_text()
    assert "OPERATIONS_REPOSITORY: Z-Solo-King/operations" in text
    assert "OPERATIONS_RESEARCH_REF: 9bb210d36f41afaa1bedc1be65e89ba6444d3f78" in text
    assert "OPERATIONS_APP_ID: ${{ secrets.OPERATIONS_APP_ID }}" in text
    assert "OPERATIONS_APP_INSTALLATION_ID" not in text
    assert "resolve_operations_installation.py" in text
    assert "GitHub App installation discovery failed" in text
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


def test_summary_validates_complete_nightly_artifact_bundle_after_baseline():
    text = workflow_text()
    marker = "name: Validate complete nightly artifact bundle"
    assert marker in text
    assert "python -m benchmark.research_artifact_validator --root ." in text
    assert text.index("name: Validate baseline contract") < text.index(marker)


def test_summary_is_always_run_and_final_gate_preserves_failure():
    text = workflow_text()
    assert "name: Diagnose nightly Heroic AI research" in text
    assert "needs: [research, migration_review]" in text
    assert "if: ${{ always() }}" in text
    assert "name: Preserve truthful nightly result" in text
    assert "needs: [research, migration_review, project-summary]" in text
    assert "One or more research lanes failed/blocked" in text
    assert "Nightly migration review failed" in text
    assert 'agent_capacities"] == [1, 2, 4, 8]' in text


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


def test_nightly_baseline_lookup_uses_only_current_registered_workflow():
    text = workflow_text()
    assert "gh run list --workflow nightly-multi-agent-research-v3.yml" in text
    assert "nightly-multi-agent-research.yml" not in text


def test_live_worker_proxy_probe_shell_expression_is_closed_and_non_aborting():
    text = workflow_text()
    assert "probe_payload=$(jq -nc '{model:\"@cf/zai-org/glm-4.7-flash\",messages:[{role:\"user\",content:\"Return exactly OK.\"}],max_tokens:1,temperature:0}')" in text
    assert 'name: Run complete research lane' in text
    assert 'cat "$RUNNER_TEMP/research-worker-proxy.log" 2>/dev/null || true\\n          exit 1' not in text
