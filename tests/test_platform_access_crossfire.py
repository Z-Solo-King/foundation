from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_live_provider_crossfire_is_a_thin_caller_and_common_runner_owns_six_slots():
    caller = (ROOT / ".github/workflows/live-ai-provider-crossfire.yml").read_text(encoding="utf-8")
    runner = (ROOT / ".github/workflows/chatbot-post-release-crossfire.yml").read_text(encoding="utf-8")
    assert "uses: ./.github/workflows/chatbot-post-release-crossfire.yml" in caller
    assert "secrets: inherit" in caller
    assert "--providers-max 6" not in caller
    assert "PROVIDER_KEYS_JSON" not in caller
    assert "OPERATIONS_CROSSFIRE_RUNNER" not in caller
    assert "--providers-max 6" in runner
    assert "PROVIDER_KEYS_JSON" in runner
    assert "OPERATIONS_CROSSFIRE_RUNNER" in runner


def test_public_crossfire_bridge_contains_no_direct_provider_credentials():
    source = (ROOT / "benchmark/ai_provider_crossfire.py").read_text(encoding="utf-8")
    assert "PROVIDER_KEYS_JSON" not in source
    assert "api.groq.com" not in source
    assert "OPERATIONS_CROSSFIRE_RUNNER" in source
