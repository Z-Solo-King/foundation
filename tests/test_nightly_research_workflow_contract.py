from pathlib import Path

WORKFLOW = Path(__file__).parents[1] / ".github" / "workflows" / "nightly-multi-agent-research-v3.yml"

def workflow_text() -> str:
    return WORKFLOW.read_text(encoding="utf-8")

def test_production_gate_is_event_driven_and_exact_sha_bound():
    text=workflow_text()
    assert "workflow_run:" not in text
    assert "production_release_run_id" in text
    assert "heroic-ai-production-release.yml" in text
    assert ".headBranch" in text
    assert "= \"main\"" in text
    assert "TARGET_FOUNDATION_SHA" in text
    assert "RELEASE_RUN_ID" in text
    assert "gh run view" in text
    assert "workflowName" in text
    assert "headSha" in text
    assert "conclusion" in text
    assert '.jobs[]? | select(.name == "Canonical Heroic AI production release")' in text
    assert 'select(.name == "Run canonical production release")' in text
    assert "timeout-minutes: 5" in text
    assert "short reconciliation" in text
    assert "seq 1 12" in text
    assert "seq 1 240" not in text

def test_crossfire_is_single_global_execution_pool():
    text=workflow_text()
    research=text.split("  research:",1)[1].split("\n  migration_review:",1)[0]
    assert "name: Nightly research CrossFire (24-program global scheduler)" in research
    assert "strategy:" not in research
    assert "--crossfire" in research
    assert "--global-capacity 20" in research
    assert "Materialize and validate lane artifacts" in research
    assert "Upload nightly research lane 0" in research
    assert "Upload nightly research lane 1" in research
    assert "Upload nightly research lane 2" in research

def test_dispatch_false_does_not_coerce_to_dry_run():
    text=workflow_text()
    assert 'if [[ "${{ inputs.dry_run }}" == "true" ]]; then' in text


def test_production_release_explicitly_dispatches_nightly_live_mode():
    release = (Path(__file__).parents[1] / ".github" / "workflows" / "heroic-ai-production-release.yml").read_text(encoding="utf-8")
    assert 'if [[ "$workflow" == "nightly-multi-agent-research-v3.yml" ]]; then' in release
    assert "--json" in release
    assert "dry_run:false" in release
    assert "--field dry_run=false" not in release


def test_private_operations_pin_and_app_auth_remain_explicit():
    text=workflow_text()
    assert "OPERATIONS_RESEARCH_REF: 8bee0ca4c41e02d2b7005589a73f53dc0512aa9d" in text
    assert "OPERATIONS_APP_ID: ${{ secrets.OPERATIONS_APP_ID }}" in text
    assert "OPERATIONS_APP_PRIVATE_KEY: ${{ secrets.OPERATIONS_APP_PRIVATE_KEY }}" in text
    assert "private.multi_agent.runner" in text
    assert "OPERATIONS_READ_TOKEN" not in text

def test_project_and_migration_jobs_use_exact_foundation_sha():
    text=workflow_text()
    assert text.count("ref: ${{ env.TARGET_FOUNDATION_SHA }}") >= 3

def test_public_failure_contract_is_preserved():
    text=workflow_text()
    assert "name: Diagnose nightly Heroic AI research" in text
    assert "name: Preserve truthful nightly result" in text
    assert "needs: [research, migration_review, project-summary]" in text
    assert "One or more research lanes failed/blocked" in text

def test_permissions_remain_job_scoped():
    text=workflow_text()
    top=text.split("jobs:",1)[0]
    assert "id-token: write" not in top
    assert "attestations: write" not in top
    research=text.split("  research:",1)[1].split("\n  migration_review:",1)[0]
    assert "id-token: write" in research
    assert "attestations: write" in research