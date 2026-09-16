from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).parents[1]
WORKFLOW_ROOT = ROOT / ".github" / "workflows"
SHA_REF = re.compile(r"^[0-9a-f]{40}$")

CANONICAL_OPERATIONS_REPOSITORY = "Z-Solo-King/operations"
CANONICAL_OPERATIONS_REF = "cf28a28cb40de527aff1cd87f96e103669635f70"
LEGACY_OPERATIONS_REF = "bb1d8c33e926a9752de86492e9d35f26a5f2824c"
PRODUCTION_WORKFLOW = "production-ui-contract.yml"
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


def test_operations_installation_is_discovered_from_app_jwt():
    frontend = _workflow_texts()[PRODUCTION_WORKFLOW]
    helper = INSTALLATION_HELPER.read_text(encoding="utf-8")
    assert "Resolve Operations GitHub App installation" in frontend
    assert "scripts/resolve_operations_installation.py" in frontend
    assert "OPERATIONS_APP_JWT" in helper
    assert "api.github.com/app/installations" in helper
    assert 'EXPECTED_ACCOUNT = "Z-Solo-King"' in helper
    assert "OPERATIONS_APP_INSTALLATION_ID: ${{ secrets.OPERATIONS_APP_INSTALLATION_ID }}" not in frontend


def test_operations_checkout_uses_github_app_installation_credential():
    deployment = PRODUCTION_SCRIPT.read_text(encoding="utf-8")
    assert "OPERATIONS_APP_ID" in deployment
    assert "OPERATIONS_APP_INSTALLATION_ID" in deployment
    assert "OPERATIONS_APP_PRIVATE_KEY" in deployment
    assert "GITHUB_APP_TOKEN" in deployment
    assert "api.github.com/repos/${OPERATIONS_REPOSITORY}" in deployment
    assert "OPERATIONS_READ_TOKEN" not in deployment


def test_frontend_ui_keeps_one_job_and_guards_release_to_main_push():
    frontend = _workflow_texts()[PRODUCTION_WORKFLOW]
    assert "name: frontend-ui" in frontend
    assert "jobs:" in frontend
    assert "contract:" in frontend
    assert "needs:" not in frontend
    assert "uses: ./.github/workflows/production-release-reusable.yml" not in frontend
    assert "gh workflow run" not in frontend
    assert "if: github.event_name == 'push' && github.ref == 'refs/heads/main'" in frontend
    assert "working-directory: ${{ github.workspace }}" in frontend
    assert "actions: write" not in frontend


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
        "OPERATIONS_APP_INSTALLATION_ID",
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
    texts = _workflow_texts()
    required = texts["required-pr-checks.yml"]
    frontend = texts[PRODUCTION_WORKFLOW]
    assert "merge_group:" in required
    assert "types: [checks_requested]" in required
    assert "name: Public tests" in required
    assert "name: Analyze python" in required
    assert "npm test" in required
    assert "merge_group:" in frontend
