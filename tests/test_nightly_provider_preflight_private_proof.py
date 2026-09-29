from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_nightly_preflight_uses_private_provider_runtime_proof():
    text = (ROOT / ".github" / "workflows" / "nightly-research-provider-preflight.yml").read_text(encoding="utf-8")
    assert "/api/v1/chatbot/diagnostic" in text
    assert 'infrastructure_verify_public_test' in text
    assert 'release_acceptance=true' in text
    assert 'provider_runtime_workers_ai' in text
    assert '.response.provider == "cloudflare_workers_ai"' not in text
