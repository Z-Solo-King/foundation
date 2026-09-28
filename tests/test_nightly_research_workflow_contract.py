from pathlib import Path

WORKFLOW = Path(__file__).parents[1] / ".github" / "workflows" / "nightly-multi-agent-research-v3.yml"

def workflow_text() -> str:
    return WORKFLOW.read_text(encoding="utf-8")

def test_production_gate_is_event_driven_and_exact_sha_bound():
    text=workflow_text()
    assert "workflow_run:" in text
    assert 'workflows: ["Heroic AI production release"]' in text
    assert "branches: [main]" in text
    assert "TARGET_FOUNDATION_SHA" in text
    assert "EVENT_RELEASE_HEAD_SHA" in text
    assert "EVENT_RELEASE_HEAD_BRANCH" in text
    assert "EVENT_RELEASE_CONCLUSION" in text
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

def test_private_operations_pin_and_app_auth_remain_explicit():
    text=workflow_text()
    assert "OPERATIONS_RESEARCH_REF: bf4af8db50d7b39c79acd09a9e90237856962abb" in text
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