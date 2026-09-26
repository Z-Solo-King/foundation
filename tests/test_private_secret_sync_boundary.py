from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "sync-secrets.yml"

def test_secret_sync_uses_private_operations_revision():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "OPERATIONS_SECRET_SYNC_REF: cb6220fec89d1aa913bfd06fc0da52fda0f176c6" in text
    assert 'clone --filter=blob:none "https://github.com/${OPERATIONS_REPOSITORY}.git"' in text
    assert 'python "$RUNNER_TEMP/operations/tools/sync_provider_secrets.py"' in text
    assert "python tools/sync_provider_secrets.py" not in text

def test_public_secret_sync_implementation_is_removed():
    assert not (ROOT / "tools" / "sync_provider_secrets.py").exists()
