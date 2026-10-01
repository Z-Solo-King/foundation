from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "provider-fleet-runtime-state.yml"


def test_provider_fleet_workflow_is_structured_and_protected() -> None:
    payload = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))

    assert "jobs" in payload
    job = payload["jobs"]["refresh"]
    assert job["environment"] == "production-secret-sync"
    assert job["timeout-minutes"] == 10
    assert payload["concurrency"]["cancel-in-progress"] is True


def test_provider_fleet_workflow_uses_immutable_private_probe() -> None:
    text = WORKFLOW.read_text(encoding="utf-8")

    assert "OPERATIONS_PROVIDER_FLEET_REF: b95e419254a9071beaeef57a1b0da22ba7dd2c4f" in text
    assert "OPERATIONS_PROVIDER_FLEET_PATH: tools/provider_fleet_runtime_probe.py" in text
    assert "Provider fleet probe verified at immutable Operations ref" in text
    assert "CHAT_PROVIDER_RUNTIME_STATE" in text
    assert "secrets.CLOUDFLARE_API_TOKEN" in text
    assert "secrets.CLOUDFLARE_ACCOUNT_ID" in text
    assert "PROVIDER_KEYS_JSON" in text
    assert "secrets.NVIDIA_NIM_API_KEY" in text
    assert "secrets.HF_TOKEN" in text
    assert "secrets.COHERE_API_KEY" in text
    assert "secrets.SILICONFLOW_API_KEY" in text
    assert "nvidia_nim" in text
    assert "huggingface_free" in text
    assert "cohere_free" in text


def test_provider_fleet_workflow_rejects_secret_leak_patterns() -> None:
    text = WORKFLOW.read_text(encoding="utf-8")
    assert 'echo "$PROVIDER_KEYS_JSON"' not in text
    assert 'cat "$PROVIDER_KEYS_JSON"' not in text
    for provider in ("GROQ", "GEMINI", "OPENROUTER", "SILICONFLOW", "NVIDIA_NIM", "COHERE", "HUGGINGFACE"):
        assert f'echo "${provider}_API_KEY"' not in text
        assert f'cat "${provider}_API_KEY"' not in text
    assert "PROVIDER_KEYS_JSON" in text


def test_provider_fleet_workflow_has_concurrency_and_bounded_schedule() -> None:
    text = WORKFLOW.read_text(encoding="utf-8")
    assert 'cron: "17 */4 * * *"' in text
    assert "provider-fleet-runtime-state-production" in text
    assert "cancel-in-progress: true" in text


def test_provider_fleet_workflow_tolerates_malformed_base_config_for_benchmark_without_partial_publish() -> None:
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "except json.JSONDecodeError:" in text
    assert "base_config_valid=" in text
    assert "if steps.validate-config.outputs.base_config_valid == 'true'" in text
    assert "Live endpoint probing will continue using explicitly configured provider overrides only." in text
    assert "provider-fleet-benchmark-${{ github.run_id }}" in text
