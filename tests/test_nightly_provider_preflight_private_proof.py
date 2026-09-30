from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_nightly_preflight_uses_private_provider_runtime_proof():
    text = (ROOT / ".github" / "workflows" / "nightly-research-provider-preflight.yml").read_text(encoding="utf-8")
    assert "nightly_runtime_contract_probe.py" in text
    assert "expected-foundation-sha" in text
    assert "expected-operations-ref" in text
    assert "api/v1/chatbot/diagnostic" not in text
