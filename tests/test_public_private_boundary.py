from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_private_secret_sync_implementation_is_not_public():
    assert not (ROOT / "tools" / "sync_provider_secrets.py").exists()


def test_secret_sync_workflow_is_a_private_operations_bridge():
    text = (ROOT / ".github" / "workflows" / "sync-secrets.yml").read_text(encoding="utf-8")
    assert "OPERATIONS_REPOSITORY: Z-Solo-King/operations" in text
    assert "OPERATIONS_SECRET_SYNC_REF: ${{ vars.OPERATIONS_SECRET_SYNC_REF }}" in text
    assert "d21bc2620b93521beabc7c36704654e327fb153e" in text
    assert "OPERATIONS_SECRET_SYNC_PATH: ${{ vars.OPERATIONS_SECRET_SYNC_PATH }}" in text
    assert "github.ref == 'refs/heads/main'" in text
    assert "environment: production-secret-sync" in text
    assert "create-github-app-token@" in text
    assert "permission-contents: read" in text
    assert "permission-secrets: write" not in text
    assert 'SKIP_GITHUB_SYNC: "1"' in text
    assert "py_compile" in text
    assert "PyNaCl==1.5.0" in text
    assert 'python "$RUNNER_TEMP/sync_provider_secrets.py"' in text


def test_secret_sync_workflow_never_executes_public_copy():
    text = (ROOT / ".github" / "workflows" / "sync-secrets.yml").read_text(encoding="utf-8")
    assert "python tools/sync_provider_secrets.py" not in text


def test_secret_sync_workflow_has_no_stale_operations_revision():
    text = (ROOT / ".github" / "workflows" / "sync-secrets.yml").read_text(encoding="utf-8")
    assert "a2f9614cac0e4ba7118de8b6b7d86c82ee2cd6f9" not in text
    assert "OPERATIONS_SECRET_SYNC_REF: ${{ vars.OPERATIONS_SECRET_SYNC_REF }}" in text
