from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).parents[1]
WORKFLOW_ROOT = ROOT / ".github" / "workflows"
SHA_REF = re.compile(r"^[0-9a-f]{40}$")

CANONICAL_OPERATIONS_REPOSITORY = "Z-Solo-King/operations"
CANONICAL_OPERATIONS_REF = "566fe7b90c15a8e0ad8210bd98a7b514de6f5fc3"
BENCHMARK_OPERATIONS_REF = CANONICAL_OPERATIONS_REF
BENCHMARK_TOOLS_REF = "d4ef2e6d28435a59c735b9dc4d0de31f44b9cf29"
MIGRATION_TOOLS_REF = None
VALIDATION_TOOLS_REF = "566fe7b90c15a8e0ad8210bd98a7b514de6f5fc3"
CANONICAL_OPERATIONS_SERVICE = "operations"
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


# Canonical Operations revision is declared once and used by the release self-check.\n\ndef test_canonical_operations_production_pin_is_current_and_immutable():
    deployment = PRODUCTION_SCRIPT.read_text(encoding="utf-8")
    assert f'OPERATIONS_REPOSITORY="{CANONICAL_OPERATIONS_REPOSITORY}"' in deployment
    assert f'OPERATIONS_REF="{CANONICAL_OPERATIONS_REF}"' in deployment
    assert deployment.count(CANONICAL_OPERATIONS_REF) == 2
    assert LEGACY_OPERATIONS_REF not in deployment
    assert 'git clone --no-checkout "https://github.com/${OPERATIONS_REPOSITORY}.git"' in deployment
    assert '"github:${OPERATIONS_REF}"' in deployment
    assert '.private == true' in deployment


def test_production_pin_self_check_matches_canonical_operations_revision():
    deployment = PRODUCTION_SCRIPT.read_text(encoding="utf-8")
    assert "test \"$OPERATIONS_REF\" = '566fe7b90c15a8e0ad8210bd98a7b514de6f5fc3'" in deployment
    assert "test \"$OPERATIONS_REF\" = 'ca9cc887049b2800361b222bbdae7f56100f4f7c'" not in deployment


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
    assert "persistence-boundary-${ACCEPTANCE_RUN_ID}" in deployment
    assert "Operations version boundary: PASS" in deployment
    assert "concurrent-chat-1.json" in deployment
    assert "concurrent-chat-2.json" in deployment
    assert "policy-block.json" in deployment
    assert 'mode:"chat"' in deployment
    assert 'require_model_generation:true' in deployment
    assert 'generation_status == \"model_generated\"' in deployment
    assert 'provider == \"cloudflare_workers_ai\"' in deployment
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
    assert 'printf \'AUTH_TOKEN=%s\\nCHAT_BACKEND_TOKEN=%s\\n\' "$AUTH_TOKEN" "$AUTH_TOKEN" > "$secret_file"' in deployment
    assert 'printf \'AUTH_TOKEN=%s\\nB2_KEY_ID=%s\\nB2_APPLICATION_KEY=%s\\n\'' in deployment
    assert 'test -n "${B2_KEY_ID:-}"' in deployment
    assert 'test -n "${B2_APPLICATION_KEY:-}"' in deployment
def test_public_worker_static_assets_binding_is_declared():
    wrangler = WRANGLER.read_text(encoding="utf-8")
    assert '[assets]' in wrangler
    assert 'directory = "./frontend"' in wrangler