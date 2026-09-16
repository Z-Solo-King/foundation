from __future__ import annotations

import re
from pathlib import Path

WORKFLOW_ROOT = Path(__file__).parents[1] / ".github" / "workflows"
SHA_REF = re.compile(r"^[0-9a-f]{40}$")

CANONICAL_OPERATIONS_REPOSITORY = "Z-Solo-King/operations"
CANONICAL_OPERATIONS_REF = "cf28a28cb40de527aff1cd87f96e103669635f70"
LEGACY_OPERATIONS_REF = "bb1d8c33e926a9752de86492e9d35f26a5f2824c"
PRODUCTION_WORKFLOW = "production-publish-v2.yml"


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
    deployers = [name for name, text in texts.items() if "pywrangler deploy" in text]
    assert deployers == [PRODUCTION_WORKFLOW], deployers

    forbidden = re.compile(r"(?i)(workers\s+build|deploy\s+hook|deploy_hook|workers-builds)")
    violations = [
        f"{name}:{line_no}:{line.strip()}"
        for name, text in texts.items()
        for line_no, line in enumerate(text.splitlines(), 1)
        if forbidden.search(line)
    ]
    assert not violations, "Competing Cloudflare deployment references:\n" + "\n".join(violations)


def test_canonical_operations_production_pin_is_current_and_immutable():
    deployment = _workflow_texts()[PRODUCTION_WORKFLOW]
    assert f"OPERATIONS_REPOSITORY: {CANONICAL_OPERATIONS_REPOSITORY}" in deployment
    assert f"OPERATIONS_REF: {CANONICAL_OPERATIONS_REF}" in deployment
    assert deployment.count(CANONICAL_OPERATIONS_REF) == 2
    assert LEGACY_OPERATIONS_REF not in deployment
    assert "OPERATIONS_REF:" not in deployment.split("jobs:", 1)[1]
    assert 'git clone --no-checkout "https://github.com/${OPERATIONS_REPOSITORY}.git"' in deployment
    assert '"github:${OPERATIONS_REF}"' in deployment


def test_operations_checkout_uses_github_app_installation_credential():
    deployment = _workflow_texts()[PRODUCTION_WORKFLOW]
    assert "OPERATIONS_APP_ID: ${{ secrets.OPERATIONS_APP_ID }}" in deployment
    assert "OPERATIONS_APP_INSTALLATION_ID: ${{ secrets.OPERATIONS_APP_INSTALLATION_ID }}" in deployment
    assert "OPERATIONS_APP_PRIVATE_KEY: ${{ secrets.OPERATIONS_APP_PRIVATE_KEY }}" in deployment
    assert "GITHUB_APP_TOKEN" in deployment
    assert "api.github.com/repos/${OPERATIONS_REPOSITORY}" in deployment
    assert "OPERATIONS_READ_TOKEN" not in deployment


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
    root = Path(__file__).parents[1]
    policy = (root / "docs" / "CREDENTIAL_AND_BACKUP_AUTHORITY.md").read_text(encoding="utf-8")
    deployment = (root / "DEPLOYMENT.md").read_text(encoding="utf-8")
    backup = (root / "backup" / "README.md").read_text(encoding="utf-8")

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
    frontend = texts["frontend-ui.yml"]
    assert "merge_group:" in required
    assert "types: [checks_requested]" in required
    assert "name: Public tests" in required
    assert "name: Analyze python" in required
    assert "npm test" in required
    assert "merge_group:" in frontend
