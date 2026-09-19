from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).parents[1]
WORKFLOW_ROOT = ROOT / ".github" / "workflows"
SHA_REF = re.compile(r"^[0-9a-f]{40}$")

CANONICAL_OPERATIONS_REPOSITORY = "Z-Solo-King/operations"
CANONICAL_OPERATIONS_REF = "617889b37c6bafefd46d8c82682af125ad91c093"
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
    assert "if:" not in frontend
    assert "needs:" not in frontend
    assert "gh workflow run" not in frontend
    assert "actions: write" not in frontend




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
    assert "return await assets.fetch(request)" in worker


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
    workflow = _workflow_texts()["foundation-canonical-workflow-bridge.yml"]
    assert "actions/create-github-app-token@bcd2ba49218906704ab6c1aa796996da409d3eb1" in workflow
    assert "FOUNDATION_APP_ID" in workflow
    assert "FOUNDATION_APP_PRIVATE_KEY" in workflow
    assert "permission-actions: write" in workflow
    assert "repositories: foundation" in workflow
    assert "workflow_dispatch:" in workflow
    assert "actions/workflows/${TARGET}/dispatches" in workflow
    for target in (
        "heroic-ai-production-release.yml",
        "nightly-multi-agent-research.yml",
        "cross-repository-contract-drift.yml",
        "operations-centralized-validation.yml",
        "main-push-actions-control-plane-probe.yml",
    ):
        assert target in workflow
    assert "confirm_production=true" in workflow
    assert "operations_ref" in workflow


def test_all_canonical_workflow_dispatch_requests_use_the_public_router():
    texts = _workflow_texts()
    dispatchers = [
        name
        for name, text in texts.items()
        if "actions/workflows/" in text and "/dispatches" in text
    ]
    assert dispatchers == ["foundation-canonical-workflow-bridge.yml"]




def test_production_release_has_live_runtime_acceptance_gates():
    production = (ROOT / "scripts" / "production_release.sh").read_text(encoding="utf-8")
    assert 'POST /api/v1/chat -> HTTP' in production
    assert 'Live chat acceptance: PASS' in production
    assert 'Live chat idempotency acceptance: PASS' in production
    assert 'POST /api/v1/chat/stream -> HTTP' in production
    assert 'Live SSE lifecycle acceptance: PASS' in production
    assert 'POST /api/v1/research -> HTTP' in production
    assert 'Live research execution/readback acceptance: PASS' in production

def test_centralized_operations_validation_owns_private_repo_ci():
    workflow = _workflow_texts()["operations-centralized-validation.yml"]
    assert "actions/create-github-app-token@bcd2ba49218906704ab6c1aa796996da409d3eb1" in workflow
    assert "OPERATIONS_APP_ID" in workflow
    assert "OPERATIONS_APP_PRIVATE_KEY" in workflow
    assert "repositories: operations" in workflow
    assert "actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1" in workflow
    assert "python -m pytest tests -q" in workflow
    assert "contents/.github/workflows?ref=${OPERATIONS_REF}" in workflow
    assert "private Operations GitHub Actions boundary: FAIL" in workflow

def test_private_operations_automation_guard_is_in_public_foundation_ci():
    workflow = _workflow_texts()["cross-repository-contract-drift.yml"]
    assert 'contents/.github/workflows?ref=main' in workflow
    assert 'private Operations GitHub Actions boundary: PASS' in workflow
    assert 'private Operations GitHub Actions boundary: FAIL' in workflow
    assert 'cron: "17 2 * * *"' in workflow

def test_required_pr_checks_emit_the_branch_protection_contract():
    required = _workflow_texts()["required-pr-checks.yml"]
    assert "pull_request:" in required
    assert "merge_group:" in required
    assert "types: [checks_requested]" in required
    assert "name: Public tests" in required
    assert "name: Analyze python" in required
    assert "pywrangler deploy" not in required
    assert "CLOUDFLARE_API_TOKEN" not in required
    assert "B2_KEY_ID" not in required


def test_backup_workflow_separates_github_and_b2_credentials():
    backup = _workflow_texts()["b2-repository-backup.yml"]
    assert "BACKUP_GITHUB_TOKEN: ${{ secrets.BACKUP_GITHUB_TOKEN }}" in backup
    assert "B2_KEY_ID: ${{ secrets.B2_KEY_ID }}" in backup
    assert "B2_APPLICATION_KEY: ${{ secrets.B2_APPLICATION_KEY }}" in backup
    assert "https://api.github.com/repos/Z-Solo-King/operations" in backup
    assert "BACKUP_GITHUB_TOKEN purpose check: PASS (GitHub repository access)" in backup
    assert "B2 credential/bucket check: PASS" in backup
    assert "OPERATIONS_READ_TOKEN" not in backup


def test_credential_policy_documents_the_separation():
    policy = (ROOT / "docs" / "CREDENTIAL_AND_BACKUP_AUTHORITY.md").read_text(encoding="utf-8")
    deployment = (ROOT / "DEPLOYMENT.md").read_text(encoding="utf-8")
    backup = (ROOT / "backup" / "README.md").read_text(encoding="utf-8")

    for secret in (
        "OPERATIONS_APP_ID",
        "OPERATIONS_APP_PRIVATE_KEY",
        "BACKUP_GITHUB_TOKEN",
        "B2_KEY_ID",
        "B2_APPLICATION_KEY",
        "CLOUDFLARE_API_TOKEN",
        "AUTH_TOKEN",
    ):
        assert secret in policy

    assert "B2 credentials are secrets and never belong in Git" in deployment
    assert "`BACKUP_GITHUB_TOKEN` is a GitHub read credential" in backup
    assert "Production deployment uses the purpose-specific GitHub App installation credential set" in backup
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
    workflow = _workflow_texts()["foundation-canonical-workflow-bridge.yml"]
    assert 'actions/workflows/${TARGET}/runs' in workflow
    assert "CONTROL_PLANE=UNKNOWN" in workflow
    assert "CONTROL_PLANE=ACCEPTED_TRIGGER_ZERO_JOB" in workflow
    assert "CONTROL_PLANE=JOB_CREATED" in workflow
    assert "head_sha" in workflow
    assert "for attempt in {1..6}; do" in workflow
    assert "no job was created after bounded polling" in workflow
    assert 'actions/runs/${run_id}/jobs' in workflow
