from pathlib import Path

ROOT = Path(__file__).parents[1]

def test_public_surface_policy_exists_and_names_private_categories():
    policy = (ROOT / "docs" / "PUBLIC_SURFACE_POLICY.md").read_text(encoding="utf-8")
    for marker in (
        "provider credentials",
        "private orchestration",
        "private prompts",
        "retailer-specific extraction selectors",
        "Commit and PR messages are part of the public surface",
    ):
        assert marker in policy

def test_security_policy_exists():
    text = (ROOT / "SECURITY.md").read_text(encoding="utf-8")
    assert "Do not publish security-sensitive findings" in text
    assert "API keys" in text
    assert "Repository history is durable" in text

def test_codeowners_covers_riskier_paths():
    text = (ROOT / ".github" / "CODEOWNERS").read_text(encoding="utf-8")
    assert "* @Z-Solo-King" in text
    assert ".github/workflows/* @Z-Solo-King" in text
    assert "tools/* @Z-Solo-King" in text

def test_privileged_secret_sync_is_main_only():
    workflow = (ROOT / ".github" / "workflows" / "sync-secrets.yml").read_text(encoding="utf-8")
    assert "github.ref == 'refs/heads/main'" in workflow
    assert 'test "$GITHUB_REF" = "refs/heads/main"' in workflow
    assert "environment: production-secret-sync" in workflow