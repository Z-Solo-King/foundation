from pathlib import Path

ROOT = Path(__file__).parents[1]
ENTRY = ROOT / "scripts" / "production_release.sh"
PREFLIGHT = ROOT / "scripts" / "release" / "production_release_preflight.sh"
DEPLOY = ROOT / "scripts" / "release" / "production_release_deploy_acceptance.sh"

def test_release_entrypoint_is_small_and_sources_two_phases():
    text = ENTRY.read_text(encoding="utf-8")
    assert len(text.splitlines()) < 40
    assert "source" in text
    assert PREFLIGHT.name in text
    assert DEPLOY.name in text

def test_release_phases_preserve_required_entrypoint_contracts():
    pre = PREFLIGHT.read_text(encoding="utf-8")
    deploy = DEPLOY.read_text(encoding="utf-8")
    assert 'OPERATIONS_REPOSITORY="Z-Solo-King/operations"' in pre
    assert "trap cleanup EXIT" in pre
    assert "# Rename-safe Cloudflare deployment sequence." in deploy
    assert "Heroic AI production release" not in pre
