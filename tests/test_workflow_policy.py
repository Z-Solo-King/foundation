from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PRODUCTION_WORKFLOW = ROOT / ".github" / "workflows" / "production-ui-contract.yml"
PRODUCTION_SCRIPT = ROOT / "scripts" / "production_release.sh"
WRANGLER = ROOT / "wrangler.toml"


def _workflow_texts() -> dict[Path, str]:
    return {PRODUCTION_WORKFLOW: PRODUCTION_WORKFLOW.read_text(encoding="utf-8")}


def test_all_third_party_actions_are_sha_pinned():
    texts = "\n".join(path.read_text(encoding="utf-8") for path in (ROOT / ".github" / "workflows").glob("*.yml"))
    for owner, action in re.findall(r"uses:\s*([^@\s]+)@([^\s#]+)", texts):
        assert re.fullmatch(r"[0-9a-f]{40}", action), f"Unpinned action: {owner}@{action}"


def test_production_deployment_has_one_owner():
    workflow_files = list((ROOT / ".github" / "workflows").glob("*.yml"))
    production_mentions = []
    for path in workflow_files:
        text = path.read_text(encoding="utf-8")
        if "scripts/production_release.sh" in text:
            production_mentions.append(path)
    assert production_mentions == [PRODUCTION_WORKFLOW]


def test_canonical_operations_production_pin_is_current_and_immutable():
    deployment = PRODUCTION_SCRIPT.read_text(encoding="utf-8")
    expected_ref = "cf28a28cb40de527aff1cd87f96e103669635f70"
    assert f'OPERATIONS_REF="{expected_ref}"' in deployment
    assert "OPERATIONS_REF=" in deployment


def test_operations_installation_is_discovered_from_app_jwt():
    deployment = PRODUCTION_SCRIPT.read_text(encoding="utf-8")
    helper = (ROOT / "scripts" / "resolve_operations_installation.py").read_text(encoding="utf-8")
    assert "OPERATIONS_APP_ID" in deployment
    assert "OPERATIONS_APP_PRIVATE_KEY" in deployment
    assert "resolve_operations_installation.py" in deployment
    assert "EXPECTED_ACCOUNT = \"Z-Solo-King\"" in helper
    assert "OPERATIONS_APP_INSTALLATION_ID: ${{ secrets.OPERATIONS_APP_INSTALLATION_ID }}" not in deployment


def test_operations_checkout_uses_github_app_installation_credential():
    deployment = PRODUCTION_SCRIPT.read_text(encoding="utf-8")
    assert "OPERATIONS_APP_ID" in deployment
    assert "OPERATIONS_APP_INSTALLATION_ID" in deployment
    assert "OPERATIONS_APP_PRIVATE_KEY" in deployment
    assert "GITHUB_APP_TOKEN" in deployment
    assert "api.github.com/repos/${OPERATIONS_REPOSITORY}" in deployment
    assert "OPERATIONS_READ_TOKEN" not in deployment


def test_frontend_ui_keeps_one_job_and_guards_release_to_main_push_or_manual_dispatch():
    frontend = _workflow_texts()[PRODUCTION_WORKFLOW]
    assert "name: frontend-ui" in frontend
    assert "jobs:" in frontend
    assert "contract:" in frontend
    assert "needs:" not in frontend
    assert "uses: ./.github/workflows/production-release-reusable.yml" not in frontend
    assert "gh workflow run" not in frontend
    assert "workflow_dispatch:" in frontend
    release_guard = "if: (github.event_name == 'push' || github.event_name == 'workflow_dispatch') && github.ref == 'refs/heads/main'"
    assert frontend.count(release_guard) == 3
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
    assert 'binding = "ASSETS"' in deployment
    assert 'directory = "./frontend"' in deployment
    assert 'curl -sS -o health.json' in deployment
    assert 'curl -sS -o readiness.json' in deployment
    assert '/api/v1/chatbot/diagnostic' in deployment


def test_required_pr_checks_emit_the_branch_protection_contract():
    required = (ROOT / ".github" / "workflows" / "required-pr-checks.yml").read_text(encoding="utf-8")
    assert "pull_request:" in required
    assert "merge_group:" in required


def test_backup_workflow_separates_github_and_b2_credentials():
    backup = (ROOT / ".github" / "workflows" / "b2-repository-backup.yml").read_text(encoding="utf-8")
    assert "GITHUB_TOKEN" in backup
    assert "B2_APPLICATION_KEY" in backup
    assert "B2_KEY_ID" in backup
    assert "CLOUDFLARE_API_TOKEN" not in backup


def test_credential_policy_documents_the_separation():
    policy = (ROOT / "docs" / "CREDENTIAL_POLICY.md").read_text(encoding="utf-8")
    assert "GitHub" in policy
    assert "Backblaze B2" in policy
    assert "Cloudflare" in policy


def test_backup_manifests_cannot_claim_remote_restore_without_test():
    text = "\n".join(path.read_text(encoding="utf-8") for path in (ROOT / "scripts").glob("*.py"))
    assert "remote restore" not in text.lower()
