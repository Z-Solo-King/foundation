from pathlib import Path
import json

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
    assert "--field dry_run=false" in release
    assert "--field target_sha=\"$GITHUB_SHA\"" in release
    assert "--field production_release_run_id=\"$GITHUB_RUN_ID\"" in release
    assert "--json" not in release
    assert "dry_run:false" not in release


def test_private_operations_pin_and_app_auth_remain_explicit():
    text=workflow_text()
    assert "OPERATIONS_RESEARCH_REF: 1a91efa53b9202f1624ddde892b0e86bd6b360f0" in text
    assert "OPERATIONS_MIGRATION_TOOLS_REF: f9f8ce0eb88b92a5d4e2e3ea5f2d397eebac5791" in text
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

def test_research_contract_probe_is_structured_not_generic_text():
    text=workflow_text()
    assert "nightly-research-contract/v2" in text
    assert "research-contract" in text
    assert "fromjson" in text
    assert 'has("findings")' in text
    assert 'has("follow_up_questions")' in text
    assert 'has("note")' in text
    assert "max_tokens:96" in text


def test_research_coverage_manifest_is_exact_and_truthful():
    text=workflow_text()
    assert "nightly-research-coverage/v1" in text
    assert "expected_program_count" in text
    assert "24" in text
    assert "missing_program_ids" in text
    assert "unexpected_program_ids" in text
    assert "duplicate_program_ids" in text
    assert "transport/challenge/provider failures are execution states" in text


def test_open_issue_runtime_requirements_are_explicit():
    text=workflow_text()
    assert "nightly-research-acceptance-requirements/v1" in text
    assert "'foundation_58'" in text
    assert "'foundation_157'" in text
    assert "'operations_597'" in text
    assert "'operations_603'" in text
    assert "pending_external_runtime" in text
    assert "'cases'" in text and "32" in text
    assert "'repeats_min'" in text and "3" in text
    assert "shadow" in text and "canary" in text and "rollback" in text


def test_proxy_has_bounded_transport_recovery():
    proxy=(Path(__file__).parents[1]/"scripts"/"research_worker_proxy.py").read_text(encoding="utf-8")
    assert "MAX_UPSTREAM_ATTEMPTS = 3" in proxy
    assert "RETRYABLE_UPSTREAM_STATUS" in proxy
    assert "Retry-After" in proxy
    assert "bounded_3_attempts" in proxy
    assert "research_agent" in proxy


def test_operations_pin_manifest_matches_research_workflow():
    workflow=workflow_text()
    manifest=json.loads((Path(__file__).parents[1]/"docs"/"OPERATIONS_PIN_MANIFEST.json").read_text(encoding="utf-8"))
    assert manifest["pins"]["research_runtime"]["sha"] == "1a91efa53b9202f1624ddde892b0e86bd6b360f0"
    assert manifest["pins"]["research_runtime"]["sha"] in workflow


def test_pinned_operations_contract_guard_is_semantic():
    text=workflow_text()
    assert "endpoint_compact" in text
    assert 'research_agent=bool(payload.get("research_agent",False))' in text
    assert "ast.parse(live)" in text
    assert '"_output_token_limit"' in text
    assert '"response_format"' in text
    assert '"findings"' in text
    assert '"follow_up_questions"' in text
    assert '"note"' in text
    assert "private/chatbot/chat_endpoint.py" in text
    assert "private/chatbot/live_answer.py" in text
t