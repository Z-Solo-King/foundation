from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_private_secret_sync_implementation_is_not_public():
    assert not (ROOT / "tools" / "sync_provider_secrets.py").exists()


def test_secret_sync_workflow_is_a_private_operations_bridge():
    text = (ROOT / ".github" / "workflows" / "sync-secrets.yml").read_text(encoding="utf-8")
    assert "OPERATIONS_REPOSITORY: Z-Solo-King/operations" in text
    assert "OPERATIONS_SECRET_SYNC_REF: cb6220fec89d1aa913bfd06fc0da52fda0f176c6" in text
    assert "OPERATIONS_SECRET_SYNC_PATH: tools/sync_provider_secrets.py" in text
    assert "github.ref == 'refs/heads/main'" in text
    assert "environment: production-secret-sync" in text
    assert "access_tokens" in text
    assert "--data '{\"repositories\":[\"operations\"]}'" in text
    assert "py_compile" in text
    assert 'python "$RUNNER_TEMP/sync_provider_secrets.py"' in text


def test_secret_sync_workflow_never_executes_public_copy():
    text = (ROOT / ".github" / "workflows" / "sync-secrets.yml").read_text(encoding="utf-8")
    assert "python tools/sync_provider_secrets.py" not in text
