from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _workflow(name: str) -> str:
    return (ROOT / ".github" / "workflows" / name).read_text(encoding="utf-8")


def test_production_release_is_not_pull_request_privileged_execution():
    text = _workflow("heroic-ai-production-release.yml")
    assert "push:" not in text
    assert "workflow_dispatch:" in text
    assert "pull_request:" not in text
    assert "pull_request_target:" not in text
    assert 'test "$GITHUB_REPOSITORY" = "Z-Solo-King/foundation"' in text
    assert 'test "$GITHUB_REF" = "refs/heads/main"' in text
    assert "concurrency:" in text
    assert "cancel-in-progress: false" in text


def test_production_release_has_only_read_github_token_permissions_and_pinned_actions():
    text = _workflow("heroic-ai-production-release.yml")
    assert "permissions:\n  contents: read" in text
    assert "actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1" in text
    assert "actions/setup-python@5fda3b95a4ea91299a34e894583c3862153e4b97" in text


def test_backup_is_daily_or_manual_only_and_separates_credential_purposes():
    text = _workflow("b2-repository-backup.yml")
    assert "push:" not in text
    assert "workflow_dispatch:" in text
    assert 'cron: "30 20 * * *"' in text
    assert "pull_request:" not in text
    assert "pull_request_target:" not in text
    assert "OPERATIONS_APP_ID" in text
    assert "OPERATIONS_APP_PRIVATE_KEY" in text
    assert "B2_APPLICATION_KEY" in text
    assert "CLOUDFLARE_API_TOKEN" not in text


def test_backup_retention_runs_only_after_verified_restore():
    text = _workflow("b2-repository-backup.yml")
    assert "remote B2 restore verification: PASS" in text
    assert text.index("remote B2 restore verification: PASS") < text.index("Retain only the latest verified backup generation")
    assert "scripts/cleanup_b2_backup_generations.py" in text
    assert "list-object-versions" in text
    assert "repository-backup/" in text
    assert "BACKUP_GITHUB_TOKEN" not in text
def test_privileged_boundary_contract_is_documented():
    text = (ROOT / "docs" / "PRIVILEGED_WORKFLOW_TRUST_BOUNDARY.md").read_text(encoding="utf-8")
    for phrase in (
        "Privileged workflows do not use `pull_request` or `pull_request_target` triggers.",
        "A pull request from a fork is untrusted input.",
        "least-privilege secret scopes",
        "remaining administration gate",
    ):
        assert phrase in text
