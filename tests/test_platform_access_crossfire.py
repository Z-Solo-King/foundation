from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_live_provider_crossfire_requests_six_provider_slots():
    workflow = (ROOT / ".github/workflows/live-ai-provider-crossfire.yml").read_text(encoding="utf-8")
    assert "--providers-max 6" in workflow
    assert "PROVIDER_KEYS_JSON" in workflow
    assert "OPERATIONS_CROSSFIRE_RUNNER" in workflow


def test_public_crossfire_bridge_contains_no_provider_credentials():
    source = (ROOT / "benchmark/ai_provider_crossfire.py").read_text(encoding="utf-8")
    assert "PROVIDER_KEYS_JSON" not in source
    assert "api.groq.com" not in source
    assert "OPERATIONS_CROSSFIRE_RUNNER" in source