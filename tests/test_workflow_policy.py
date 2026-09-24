from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).parents[1]
WORKFLOW_ROOT = ROOT / ".github" / "workflows"
SHA_REF = re.compile(r"^[0-9a-f]{40}$")

CANONICAL_OPERATIONS_REPOSITORY = "Z-Solo-King/operations"
CANONICAL_OPERATIONS_REF = "1a12b98981f52de207fa8626cf2e1f5ad06659be"
BENCHMARK_OPERATIONS_REF = CANONICAL_OPERATIONS_REF
BENCHMARK_TOOLS_REF = "d4ef2e6d28435a59c735b9dc4d0de31f44b9cf29"
MIGRATION_TOOLS_REF = None
VALIDATION_TOOLS_REF = "92eb7a850dff11a10886a952d5db8a42dae2b318"
CANONICAL_OPERATIONS_SERVICE = "research-intelligence-engine-private"
LEGACY_OPERATIONS_REF = "bb1d8c33e926a9752de86492e9d35f26a5f2824c"
PRODUCTION_WORKFLOW = "heroic-ai-production-release.yml"
PRODUCTION_SCRIPT = ROOT / "scripts" / "production_release.sh"
WRANGLER = ROOT / "wrangler.toml"
INSTALLATION_HELPER = ROOT / "scripts" / "resolve_operations_installation.py"


def _workflow_texts() -> dict[str, str]:
    return {
        path.name: path.read_text(encoding="utf-8")
        for path in sorted(WORKFLOW_ROOT.glob("*.y*ml"))
    }


def test_all_third_party_actions_are_sha_pinned():
    violations = []
    for name, text in _workflow_texts().items():
        for line_no, line in enumerate(text.splitlines(), 1):
            stripped = line.strip()
            if not stripped.startswith("uses:"):
                continue
            ref = stripped.split("@", 1)[-1].split("#", 1)[0].strip()
            action = stripped.split("uses:", 1)[1].split("@", 1)[0].strip()
            if action.startswith("./") or action.startswith("docker://"):
                continue
            if not SHA_REF.fullmatch(ref):
                violations.append(f"{name}:{line_no}:{action}@{ref}")
    assert not violations, "Unpinned third-party GitHub Actions:\n" + "\n".join(violations)


def test_production_deployment_has_one_owner():
    texts = _workflow_texts()
    assert "bash scripts/production_release.sh" in texts[PRODUCTION_WORKFLOW]
    assert "pywrangler deploy" in PRODUCTION_SCRIPT.read_text(encoding="utf-8")
    assert all("pywrangler deploy" not in text for name, text in texts.items() if name != PRODUCTION_WORKFLOW)
    assert "prepare-live-chat-source-fix.yml" not in texts

    forbidden = re.compile(r"(?i)(workers\s+build|deploy\s+hook|deploy_hook|workers-builds)")
    violations = [
        f"{name}:{line_no}:{line.strip()}"
        for name, text in texts.items()
        for line_no, line in enumerate(text.splitlines(), 1)
        if forbidden.search(line)
    ]
    assert not violations, "Competing Cloudflare deployment references:\n" + "\n".join(violations)


def test_canonical_operations_production_pin_is_current_and_immutable():
    deployment = PRODUCTION_SCRIPT.read_text(encoding="utf-8")
    assert f'OPERATIONS_REPOSITORY="{CANONICAL_OPERATIONS_REPOSITORY}"' in deployment
    assert f'OPERATIONS_REF="{CANONICAL_OPERATIONS_REF}"' in deployment
    assert deployment.count(CANONICAL_OPERATIONS_REF) == 2
    assert LEGACY_OPERATIONS_REF not in deployment
    assert 'git clone --no-checkout "https://github.com/${OPERATIONS_REPOSITORY}.git"' in deployment
    assert '"github:${OPERATIONS_REF}"' in deployment
    assert '.private == true' in deployment


def test_production_generates_private_operations_service_binding():
    deployment = PRODUCTION_SCRIPT.read_text(encoding="utf-8")
    assert f'OPERATIONS_SERVICE_NAME="{CANONICAL_OPERATIONS_SERVICE}"' in deployment
    assert "'[[services]]'" in deployment
    assert "'binding = \"OPERATIONS\"'" in deployment
    assert '"service = \\\"${OPERATIONS_SERVICE_NAME}\\\""' in deployment
    assert 'grep -q "^service = \\\"${OPERATIONS_SERVICE_NAME}\\\"$" wrangler.production.generated.toml' in deployment


def test_operations_installation_is_discovered_from_app_jwt():
    workflow = _workflow_texts()[PRODUCTION_WORKFLOW]
    deployment = PRODUCTION_SCRIPT.read_text(encoding="utf-8")
    helper = INSTALLATION_HELPER.read_text(encoding="utf-8")
    assert 'OPERATIONS_APP_ID: ${{ secrets.OPERATIONS_APP_ID }}' in workflow
    assert 'OPERATIONS_APP_PRIVATE_KEY: ${{ secrets.OPERATIONS_APP_PRIVATE_KEY }}' in workflow
    assert "OPERATIONS_APP_INSTALLATION_ID" not in workflow
    assert "OPERATIONS_APP_JWT" in deployment
    assert "resolve_operations_installation.py" in deployment
    assert "api.github.com/app/installations" in deployment
    assert 'EXPECTED_ACCOUNT = "Z-Solo-King"' in helper


def test_operations_checkout_uses_github_app_installation_credential():
    deployment = PRODUCTION_SCRIPT.read_text(encoding="utf-8")
    assert "OPERATIONS_APP_ID" in deployment
    assert "OPERATIONS_APP_PRIVATE_KEY" in deployment
    assert "GITHUB_APP_TOKEN" in deployment
    assert "api.github.com/repos/${OPERATIONS_REPOSITORY}" in deployment
    assert "OPERATIONS_READ_TOKEN" not in deployment


def test_production_release_has_one_minimal_main_push_job():
    frontend = _workflow_texts()[PRODUCTION_WORKFLOW]
    assert "name: Heroic AI production release" in frontend
    assert "push:" in frontend
    assert "branches: [main]" in frontend
    assert "workflow_dispatch:" in frontend
    assert "jobs:" in frontend
    assert "release:" in frontend
    assert "runs-on: ubuntu-latest" in frontend
    assert "actions/checkout@" in frontend
    assert "actions/setup-python@" in frontend
    assert "bash scripts/production_release.sh" in frontend
    assert "pull_request:" not in frontend
    assert "merge_group:" not in frontend
    assert not re.search(r"^      if:", frontend, re.MULTILINE)  # no job-level conditional; receipt steps may use step-level always()
    assert "        if: always()" in frontend
    assert "Publish sanitized production receipt" in frontend
    assert "needs:" not in frontend
    assert "gh workflow run" not in frontend
    assert "actions: write" not in frontend




def test_production_release_fails_closed_and_retains_chat_policy_receipts():
    deployment = PRODUCTION_SCRIPT.read_text(encoding="utf-8")
    workflow = (ROOT / ".github/workflows/heroic-ai-production-release.yml").read_text(encoding="utf-8")
    assert "ALLOW_PERSISTENCE_DEFERRED" not in deployment
    assert "automatic bootstrap rollover" in deployment
    assert "persistence-bootstrap-${ACCEPTANCE_RUN_ID}" in deployment
    assert "did not create a new Worker version" in deployment
    assert "concurrent-chat-1.json" in deployment
    assert "concurrent-chat-2.json" in deployment
    assert "policy-block.json" in deployment
    assert 'mode:"chat"' in deployment
    assert "policy denial -> HTTP" in deployment
    assert "policy-block.body" in deployment
    assert "d1_reservation_reject_changes_semantics" in deployment
    assert "production-runtime-acceptance-receipts" in workflow
    assert "allow_persistence_deferred" not in workflow
    assert "inputs:" not in workflow.split("permissions:", 1)[0]

def test_public_worker_propagates_client_request_cancellation_to_operations():
    worker = (ROOT / "worker.py").read_text(encoding="utf-8")
    wrangler = WRANGLER.read_text(encoding="utf-8")
    deployment = PRODUCTION_SCRIPT.read_text(encoding="utf-8")
    assert 'signal=getattr(request, "signal", None)' in worker
    assert 'if signal is not None:\n            init["signal"] = signal' in worker
    assert "enable_request_signal" in wrangler
    assert "request_signal_passthrough" in wrangler
    assert "enable_request_signal" in deployment
    assert "request_signal_passthrough" in deployment

def test_public_production_deploy_injects_required_b2_secrets():
    workflow = _workflow_texts()[PRODUCTION_WORKFLOW]
    deployment = PRODUCTION_SCRIPT.read_text(encoding="utf-8")
    assert "B2_KEY_ID: ${{ secrets.B2_KEY_ID }}" in workflow
    assert "B2_APPLICATION_KEY: ${{ secrets.B2_APPLICATION_KEY }}" in workflow
    assert "--secrets-file \"$public_secret_file\"" in deployment
    assert 'printf \'AUTH_TOKEN=%s\\nB2_KEY_ID=%s\\nB2_APPLICATION_KEY=%s\\n\'' in deployment
    assert 'test -n "${B2_KEY_ID:-}"' in deployment
    assert 'test -n "${B2_APPLICATION_KEY:-}"' in deployment
def test_public_worker_static_assets_binding_is_declared():
    wrangler = WRANGLER.read_text(encoding="utf-8")
    assert '[assets]' in wrangler
    assert 'directory = "./frontend"' in wrangler
    assert 'binding = "ASSETS"' in wrangler
    assert 'not_found_handling = "single-page-application"' in wrangler

    worker = (ROOT / "worker.py").read_text(encoding="utf-8")
    assert 'getattr(self.env, "ASSETS", None)' in worker
    assert "response = await assets.fetch(request)" in worker
    assert "Content-Security-Policy" in worker
    assert 'X-Frame-Options\"] = "DENY"' in worker


def test_production_script_preserves_static_asset_binding_and_diagnostic_smokes():
    deployment = PRODUCTION_SCRIPT.read_text(encoding="utf-8")
    assert "set -euo pipefail" in deployment
    assert "python -m pip install pytest pytest-asyncio coverage workers-py workers-runtime-sdk uv" in deployment
    assert "uv --version" in deployment
    assert 'binding = "ASSETS"' in deployment
    assert 'health_status=$(curl -sS -o health.json' in deployment
    assert 'readiness=$(curl -sS -o readiness.json' in deployment
    assert 'ui=$(curl -sS -o frontend.html' in deployment
    assert 'for asset in styles.css app.js composer.js lifecycle_controller.js; do' in deployment
    assert 'echo "GET /${asset} -> HTTP ${asset_status}"' in deployment
    assert "<title>Heroic AI — Chat & Research</title>" in deployment
    assert 'GET GitHub App installation metadata -> HTTP' in deployment
    assert 'POST GitHub App installation token -> HTTP' in deployment



def test_private_operations_deployment_verifies_cloudflare_provenance():
    deployment = PRODUCTION_SCRIPT.read_text(encoding="utf-8")
    assert 'workers/scripts/${OPERATIONS_SERVICE_NAME}/deployments' in deployment
    assert 'workers/scripts/${OPERATIONS_SERVICE_NAME}/versions/' in deployment
    assert 'workers/message' in deployment
    assert 'workers/tag' in deployment
    assert 'Operations Cloudflare provenance: PASS' in deployment


def test_private_operations_handoff_is_preflighted_and_diagnostic_runs_last():
    deployment = PRODUCTION_SCRIPT.read_text(encoding="utf-8")
    preflight = deployment.index("Preflight and stage the private Operations handoff")
    public_deploy = deployment.index("pywrangler deploy --config wrangler.production.generated.toml")
    operations_deploy = deployment.index("pywrangler deploy --config wrangler.toml --secrets-file")
    diagnostic = deployment.index("infrastructure_verify_public_test")
    success = deployment.rindex("Production release completed")
    assert preflight < public_deploy
    assert public_deploy < operations_deploy < diagnostic < success



def test_public_foundation_is_the_only_github_actions_bridge_owner():
    workflow = _workflow_texts()["foundation-canonical-workflow-bridge-v3.yml"]
    assert "name: Foundation canonical workflow bridge v3" in workflow
    assert "permissions:" in workflow
    assert "actions: write" in workflow
    assert "workflow-dispatch-bridge-receipt/v2" in workflow
    assert "canonical-bridge-v3-receipt" in workflow
    assert "workflow_dispatch:" in workflow
    assert "actions/workflows/${TARGET}/dispatches" in workflow
    for target in (
        "nightly-multi-agent-research-v2.yml",
        "main-push-actions-control-plane-probe-v2.yml",
    ):
        assert target in workflow
    assert "foundation-canonical-workflow-bridge-v2.yml" not in workflow
    assert "foundation-canonical-workflow-bridge.yml" not in workflow


def test_all_canonical_workflow_dispatch_requests_use_the_public_router():
    texts = _workflow_texts()
    raw_dispatch_callers = [
        name
        for name, text in texts.items()
        if "actions/workflows/" in text and "/dispatches" in text
        and "foundation-canonical-workflow-bridge" not in name
    ]
    assert raw_dispatch_callers == []
    acceptance = texts["canonical-workflow-dispatch-acceptance.yml"]
    assert "gh workflow run foundation-canonical-workflow-bridge-v3.yml" in acceptance



def test_backup_workflow_uses_app_auth_for_private_operations_and_separates_b2_credentials():
    backup = _workflow_texts()["b2-repository-backup.yml"]
    assert "OPERATIONS_APP_ID" in backup
    assert "OPERATIONS_APP_PRIVATE_KEY" in backup
    assert "B2_KEY_ID" in backup
    assert "B2_APPLICATION_KEY" in backup
    assert "https://api.github.com/repos/Z-Solo-King/operations" in backup
    assert "GitHub App private Operations credential: PASS" in backup
    assert "B2 credential/bucket check: PASS" in backup
    assert "BACKUP_GITHUB_TOKEN" not in backup
    assert "OPERATIONS_READ_TOKEN" not in backup
def test_credential_policy_documents_the_separation():
    policy = (ROOT / "docs" / "CREDENTIAL_AND_BACKUP_AUTHORITY.md").read_text(encoding="utf-8")
    deployment = (ROOT / "DEPLOYMENT.md").read_text(encoding="utf-8")
    backup = (ROOT / "backup" / "README.md").read_text(encoding="utf-8")

    for secret in (
        "OPERATIONS_APP_ID",
        "OPERATIONS_APP_PRIVATE_KEY",
        "B2_KEY_ID",
        "B2_APPLICATION_KEY",
        "CLOUDFLARE_API_TOKEN",
        "AUTH_TOKEN",
    ):
        assert secret in policy

    assert "B2 credentials are secrets and never belong in Git" in deployment
    assert "`OPERATIONS_APP_ID`" in policy
    assert "purpose-specific GitHub App credential family" in backup
    assert CANONICAL_OPERATIONS_REF in deployment


def test_backup_manifests_cannot_claim_remote_restore_without_test():
    workflow = _workflow_texts()["b2-repository-backup.yml"]
    assert '"remote_b2_restore_verified": False' in workflow
    assert "remote B2 restore verification: PASS" in workflow


def test_required_ci_contract_supports_merge_group():
    required = _workflow_texts()["required-pr-checks.yml"]
    assert "merge_group:" in required
    assert "types: [checks_requested]" in required
    assert "name: Public tests" in required
    assert "name: Analyze python" in required
    assert "npm test" in required


def test_operations_installation_discovery_surfaces_failures():
    deployment = PRODUCTION_SCRIPT.read_text(encoding="utf-8")
    helper = INSTALLATION_HELPER.read_text(encoding="utf-8")
    assert 'installation_status=$?' in deployment
    assert 'GitHub App installation discovery failed' in deployment
    assert '2>/dev/null || true' in deployment
    assert 'file=sys.stderr' in helper


def test_operations_public_core_is_materialized_before_worker_deploy():
    deployment = PRODUCTION_SCRIPT.read_text(encoding="utf-8")
    assert 'scripts/sync_public_core.py' in deployment
    assert 'python "$RUNNER_TEMP/operations/scripts/sync_public_core.py"' in deployment
    assert 'test -f "$RUNNER_TEMP/operations/foundation_core/__init__.py"' in deployment


def test_foundation_bridge_records_run_and_job_creation_control_plane_evidence():
    workflow = _workflow_texts()["foundation-canonical-workflow-bridge-v3.yml"]
    assert 'actions/workflows/${TARGET}/dispatches' in workflow
    assert 'actions/workflows/${TARGET}/runs' in workflow
    assert 'actions/runs/${target_run_id}/jobs' in workflow
    assert 'dispatch_status=$(curl' in workflow
    assert 'test "$dispatch_status" = "204"' in workflow
    assert 'expected_sha="$(gh api ' in workflow
    assert '/git/ref/heads/${FOUNDATION_REF}' in workflow
    assert 'target_run_id' in workflow
    assert 'target_job_count' in workflow


def test_hardened_workflows_have_timeout_and_concurrency_contract():
    texts = _workflow_texts()
    affected = {
        "codeql.yml",
        "context-budget.yml",
        "required-pr-checks.yml",
        "autonomous-scorecard.yml",
        "canonical-nightly-pin-repair.yml",
        "release-quality-regression.yml",
        "nightly-research-contract.yml",
        "main-push-actions-control-plane-probe-v2.yml",
        "cross-repository-contract-drift.yml",
        "coverage-driven-runtime-matrix.yml",
        "live-extractor-benchmark.yml",
        "canonical-workflow-dispatch-acceptance.yml",
        "hybrid-language-pilots.yml",
    }
    for name in affected:
        text = texts[name]
        assert "concurrency:" in text, name
        assert len(re.findall(r"^\s+runs-on:\s+\S+\s*$", text, re.MULTILINE)) == len(
            re.findall(r"^\s+timeout-minutes:\s+\d+\s*$", text, re.MULTILINE)
        ), name


def test_superseded_nightly_variants_are_retired():
    texts = _workflow_texts()
    assert "nightly-multi-agent-research-v3.yml" not in texts
    assert "nightly-research-v4.yml" not in texts


def test_live_extractor_benchmark_overlays_versioned_http_and_browser_producers():
    workflow = _workflow_texts()["live-extractor-benchmark.yml"]
    assert "Checkout versioned benchmark tooling" in workflow
    assert "Overlay benchmark producer tooling" in workflow
    assert "scripts/browser_site_benchmark.py" in workflow
    assert "scripts/site_benchmark_execution.py" in workflow
    assert BENCHMARK_TOOLS_REF in workflow


def test_live_extractor_benchmark_overlays_versioned_producer_tooling():
    workflow = _workflow_texts()["live-extractor-benchmark.yml"]
    assert "Checkout versioned benchmark tooling" in workflow
    assert "Overlay benchmark producer tooling" in workflow
    assert "scripts/browser_site_benchmark.py" in workflow
    assert BENCHMARK_TOOLS_REF in workflow


def test_live_extractor_benchmark_uses_versioned_runtime_and_tool_pins():
    workflow = _workflow_texts()["live-extractor-benchmark.yml"]
    production = PRODUCTION_SCRIPT.read_text(encoding="utf-8")
    extractor_ref = BENCHMARK_OPERATIONS_REF
    expected = "OPERATIONS_REF: ${{ inputs.operations_ref || '" + extractor_ref + "' }}"
    tools_expected = "benchmark_tools_ref:"
    assert expected in workflow
    assert tools_expected in workflow
    assert extractor_ref in workflow
    assert BENCHMARK_TOOLS_REF in workflow
    assert CANONICAL_OPERATIONS_REF in production


def test_nightly_migration_review_uses_separate_immutable_tooling_pin():
    workflow = _workflow_texts()["nightly-multi-agent-research-v2.yml"]
    match = re.search(r"^  OPERATIONS_MIGRATION_TOOLS_REF: ([0-9a-f]{40})$", workflow, re.MULTILINE)
    assert match is not None
    migration_tools_ref = match.group(1)
    assert migration_tools_ref != "3a7e350ddd5648caf93f58651323425186544f66"
    assert migration_tools_ref != CANONICAL_OPERATIONS_REF
    assert "Checkout pinned Operations migration tooling" in workflow
    assert "Verify Operations migration-tools revision" in workflow


def test_canonical_operations_pin_matches_latest_migration_head():
    deployment = PRODUCTION_SCRIPT.read_text(encoding="utf-8")
    assert f'OPERATIONS_REF="{CANONICAL_OPERATIONS_REF}"' in deployment
    nightly = texts = _workflow_texts()["nightly-multi-agent-research-v2.yml"]
    assert "OPERATIONS_RESEARCH_REF: 41db817dee6aa7d369ea9a07dd072b58ece1695a" in nightly



def test_coverage_runtime_matrix_uses_versioned_validation_tests():
    workflow = _workflow_texts()["coverage-driven-runtime-matrix.yml"]
    assert "validation_tools_ref:" in workflow
    assert "VALIDATION_TOOLS_REF" in workflow
    assert VALIDATION_TOOLS_REF in workflow
    assert "Checkout versioned validation tests" in workflow
    assert "Overlay exact validation test files" in workflow

def test_coverage_runtime_matrix_validates_immutable_operations_pin():
    workflow = _workflow_texts()["coverage-driven-runtime-matrix.yml"]
    assert "Validate immutable Operations acceptance pin" in workflow
    assert '[[ ! "$PINNED_OPERATIONS_REF" =~ ^[0-9a-f]{40}$ ]]' in workflow
    assert "Unpromoted Operations main drift" in workflow
    assert "stale_operations_pin" not in workflow
    assert "operations_runtime_drift" not in workflow
    assert "BLOCKED" in workflow
    assert "Idempotency-Key: $key-idem" in workflow
    assert "chat-rollover-before.json" in PRODUCTION_SCRIPT.read_text(encoding="utf-8")
    assert "chat-rollover-after.json" in PRODUCTION_SCRIPT.read_text(encoding="utf-8")

def test_production_operations_compile_guard_is_executable():
    deployment = PRODUCTION_SCRIPT.read_text(encoding="utf-8")
    assert "# Fail before deployment if the pinned Operations tree contains any Python syntax error.\\npython" not in deployment
    assert '# Fail before deployment if the pinned Operations tree contains any Python syntax error.\npython -m compileall -q "$RUNNER_TEMP/operations"' in deployment


def test_polyglot_migration_review_uses_declared_operations_python_runtime():
    workflow = _workflow_texts()["polyglot-migration-review.yml"]
    assert 'actions/setup-python@' in workflow
    assert 'python-version: "3.14"' in workflow
    setup_index = workflow.index('python-version: "3.14"')
    install_index = workflow.index("python -m pip install --disable-pip-version-check -e . --no-deps")
    assert setup_index < install_index


def test_production_release_publishes_immutable_runtime_identity():
    deployment = PRODUCTION_SCRIPT.read_text(encoding="utf-8")
    assert 'RELEASE_FOUNDATION_SHA' in deployment
    assert 'RELEASE_OPERATIONS_REF' in deployment
    assert '"RELEASE_FOUNDATION_SHA = \\"${GITHUB_SHA}\\""' in deployment
    assert '"RELEASE_OPERATIONS_REF = \\"${OPERATIONS_REF}\\""' in deployment


def test_live_acceptance_is_gated_by_runtime_provenance():
    diagnostics = (ROOT / "backend" / "worker_diagnostics.py").read_text(encoding="utf-8")
    coverage = (ROOT / ".github/workflows/coverage-driven-runtime-matrix.yml").read_text(encoding="utf-8")
    assert "RELEASE_FOUNDATION_SHA" in diagnostics
    assert "RELEASE_OPERATIONS_REF" in diagnostics
    assert 'payload["release"]' in diagnostics
    assert ".release.foundation_sha == $foundation" in coverage
    assert ".release.operations_ref == $operations" in coverage
    assert "Live runtime provenance does not match the immutable revisions under test." in coverage


def test_production_release_requires_concurrent_d1_overlimit_evidence():
    deployment = PRODUCTION_SCRIPT.read_text(encoding="utf-8")
    assert 'd1_concurrent_overlimit_changes_semantics' in deployment
def test_runtime_and_nightly_auxiliary_pins_are_not_stale():
    expected_production = "1a12b98981f52de207fa8626cf2e1f5ad06659be"
    expected_nightly = "41db817dee6aa7d369ea9a07dd072b58ece1695a"
    auxiliary = {
        "live-chatbot-production-smoke.yml": expected_production,
        "coverage-driven-runtime-matrix.yml": expected_production,
        "polyglot-governance-audit.yml": expected_production,
        "live-nightly-research-canary.yml": expected_nightly,
        "nightly-research-provider-preflight.yml": expected_nightly,
    }
    for filename, expected in auxiliary.items():
        workflow = (WORKFLOW_ROOT / filename).read_text(encoding="utf-8")
        assert expected in workflow
        assert "50e642dfb05846963a82fe76f4f5fe085d4b9a8c" not in workflow
def test_github_app_token_inputs_use_client_id():
    for name, text in _workflow_texts().items():
        if "actions/create-github-app-token@" in text:
            assert "app-id: $" + "{{ secrets.OPERATIONS_APP_ID }}" not in text, name
            assert "client-id: $" + "{{ secrets.OPERATIONS_APP_ID }}" in text, name
def test_live_extractor_benchmark_normalizes_case_receipts_before_upload():
    workflow = _workflow_texts()["live-extractor-benchmark.yml"]
    assert "name: Normalize extractor receipts" in workflow
    assert "benchmark-output/receipts.jsonl" in workflow
    assert "find benchmark-output -type f -name 'shard-*.jsonl'" in workflow
    assert "No extractor JSONL receipt was produced for this case" in workflow
    assert "find ../benchmark-artifacts -type f -name 'receipts.jsonl'" in workflow
    assert "find ../benchmark-artifacts -type f -name '*.jsonl'" not in workflow
    assert "receipt_files=()" in workflow
    assert 'test "${#receipt_files[@]}" -eq 40' in workflow
    assert 'for file in "${receipt_files[@]}"' in workflow
    assert 'test "${#inputs[@]}" -eq 40' not in workflow
def test_live_extractor_benchmark_uses_direct_callable_import_preflight():
    workflow = _workflow_texts()["live-extractor-benchmark.yml"]
    assert 'importlib.import_module("extractor_mapper.fast_engine")' in workflow
    assert 'from extractor_mapper.fast_engine import extract_and_map' in workflow
    assert 'extractor module:' in workflow
    assert 'extractor symbol type:' in workflow
def test_live_extractor_benchmark_uses_case_mode_matrix_condition():
    workflow = _workflow_texts()["live-extractor-benchmark.yml"]
    assert "if: matrix.case.mode == 'http'" in workflow
    assert "if: matrix.case.mode == 'browser'" in workflow
    assert "if: matrix.mode == 'http'" not in workflow
    assert "if: matrix.mode == 'browser'" not in workflow
def test_production_acceptance_keys_include_run_attempt():
    deployment = PRODUCTION_SCRIPT.read_text(encoding="utf-8")
    assert 'ACCEPTANCE_RUN_ID="${GITHUB_RUN_ID}-attempt-${GITHUB_RUN_ATTEMPT:-1}"' in deployment
    assert 'production-concurrent-${ACCEPTANCE_RUN_ID}' in deployment
    assert 'production-policy-${ACCEPTANCE_RUN_ID}' in deployment
    assert 'production-research-${ACCEPTANCE_RUN_ID}' in deployment
    assert 'persistence-bootstrap-${ACCEPTANCE_RUN_ID}' in deployment
    assert 'env.ACCEPTANCE_RUN_ID' not in deployment
def test_stream_probe_uses_explicit_response_identity_argument():
    deployment = PRODUCTION_SCRIPT.read_text(encoding="utf-8")
    assert 'expected_stream_response_id="chat-production-stream-request-${ACCEPTANCE_RUN_ID}"' in deployment
    assert 'jq -e --arg expected_response_id "$expected_stream_response_id"' in deployment
    assert 'env.ACCEPTANCE_RUN_ID' not in deployment


def test_live_probe_acceptance_does_not_depend_on_issue_comment_permissions():
    texts = _workflow_texts()
    assert 'gh api "repos/$GITHUB_REPOSITORY/issues/197/comments"' not in texts["public-worker-live-probe.yml"]
    assert 'gh api "repos/$GITHUB_REPOSITORY/issues/197/comments"' not in texts["live-chatbot-production-smoke.yml"]


def test_exhaustive_audit_does_not_infer_operations_branch_from_foundation_pr():
    workflow = (Path(__file__).resolve().parents[1] / ".github" / "workflows" / "exhaustive-six-lane-audit.yml").read_text(encoding="utf-8")
    assert 'context.payload.pull_request?.head?.ref' not in workflow
    assert 'github.rest.repos.getBranch' not in workflow
    assert 'core.setOutput("ref", "main")' in workflow


def test_nightly_research_uses_existing_cloudflare_workers_ai_credentials():
    workflow = (WORKFLOW_ROOT / "nightly-multi-agent-research-v2.yml").read_text(encoding="utf-8")
    preflight = (WORKFLOW_ROOT / "nightly-research-provider-preflight.yml").read_text(encoding="utf-8")
    canary = (WORKFLOW_ROOT / "live-nightly-research-canary.yml").read_text(encoding="utf-8")
    for text in (workflow, preflight, canary):
        assert "secrets.RESEARCH_LLM_ENDPOINT" not in text
        assert "secrets.RESEARCH_LLM_API_KEY" not in text
        assert "secrets.RESEARCH_LLM_MODEL" not in text
        assert "secrets.CLOUDFLARE_API_TOKEN" in text
        assert "secrets.CLOUDFLARE_ACCOUNT_ID" in text
        assert "@cf/meta/llama-3.1-8b-instruct-fast" in text
    assert "https://api.cloudflare.com/client/v4/accounts/${{ secrets.CLOUDFLARE_ACCOUNT_ID }}/ai/v1" in workflow
    assert "/chat/completions" in preflight
    assert "Cloudflare Workers AI inference probe: PASS" in preflight