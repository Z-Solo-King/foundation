from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RELEASE = ROOT / "scripts" / "production_release.sh"


def test_production_release_consumes_operations_provider_contract() -> None:
    text = RELEASE.read_text(encoding="utf-8")
    assert "approved_zero_cost_provider_values" in text
    assert 'test "$actual_provider_list" = "$expected_provider_list"' in text
    assert '"d1_reads":50000' in text
    assert '"d1_writes":1000' in text
    assert '"browser_minutes":0' in text
    assert '"workers_ai_neurons":100' in text
    assert '"model_calls":100' in text
    assert '"search_calls":500' in text


def test_production_release_does_not_hard_code_single_provider_allowlist() -> None:
    text = RELEASE.read_text(encoding="utf-8")
    assert 'CHAT_LLM_PROVIDERS = "cloudflare_workers_ai"' not in text