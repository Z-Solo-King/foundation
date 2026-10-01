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
    assert "if: always() && hashFiles('provider-runtime-state.json') != ''" in text
    assert "Only sanitized runtime state from explicitly configured providers will be published." in text
    assert "provider-fleet-benchmark-${{ github.run_id }}" in text


def test_provider_fleet_workflow_has_unique_benchmark_artifact_and_transport_diagnostic() -> None:
    text = WORKFLOW.read_text(encoding="utf-8")
    assert text.count('name: provider-fleet-benchmark-${{ github.run_id }}') == 1
    assert text.count("provider-probe-diagnostic.json") >= 2
    assert 'provider-probe-diagnostic/v1' in text


def test_provider_fleet_workflow_publishes_partial_runtime_state_safely() -> None:
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "provider-runtime-state.json" in text
    assert "Only sanitized runtime state from explicitly configured providers will be published." in text
    assert "secret_text" in text
    assert "api_key" not in text.split("Publish runtime state to private Operations Worker", 1)[1].split("Upload provider evidence", 1)[0]


def test_provider_fleet_workflow_uses_cloudflare_secret_collection_endpoint() -> None:
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "/workers/scripts/$CLOUDFLARE_SCRIPT_NAME/secrets" in text
    assert "/secrets/CHAT_PROVIDER_RUNTIME_STATE" not in text
    assert 'name:"CHAT_PROVIDER_RUNTIME_STATE",text:$text,type:"secret_text"' in text
