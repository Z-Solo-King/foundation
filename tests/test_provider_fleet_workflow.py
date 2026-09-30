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

    assert "OPERATIONS_PROVIDER_FLEET_REF: 05bb78285cb3d42c0b90a9975bb28121895dfe53" in text
    assert "OPERATIONS_PROVIDER_FLEET_PATH: tools/provider_fleet_probe.py" in text
    assert "Provider fleet probe verified at immutable Operations ref" in text
    assert "CHAT_PROVIDER_RUNTIME_STATE" in text
    assert "CF_API_TOKEN" in text
    assert "PROVIDER_KEYS_JSON" in text
    assert "secrets.NVIDIA_NIM_API_KEY" in text
    assert "secrets.HF_TOKEN" in text
    assert "secrets.COHERE_API_KEY" in text
    assert "nvidia_nim" in text
    assert "huggingface_free" in text
    assert "cohere_free" in text


def test_provider_fleet_workflow_rejects_secret_leak_patterns() -> None:
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "echo \"$PROVIDER_KEYS_JSON\"" not in text
    assert "cat \"$PROVIDER_KEYS_JSON\"" not in text
    for provider in ("GROQ", "GEMINI", "CEREBRAS", "OPENROUTER", "SILICONFLOW", "MISTRAL"):
        assert f"secrets.{provider}_API_KEY" not in text
    assert "PROVIDER_KEYS_JSON" in text


def test_provider_fleet_workflow_has_concurrency_and_bounded_schedule() -> None:
    text = WORKFLOW.read_text(encoding="utf-8")
    assert 'cron: "17 */4 * * *"' in text
    assert "provider-fleet-runtime-state-production" in text
    assert "cancel-in-progress: true" in text


def test_provider_fleet_workflow_exposes_only_the_eight_active_external_provider_inputs() -> None:
    text = WORKFLOW.read_text(encoding="utf-8")
    for name in ("PROVIDER_KEYS_JSON", "NVIDIA_NIM_API_KEY", "HF_TOKEN", "COHERE_API_KEY"):
        assert name in text
    assert '{"groq","gemini","cerebras","openrouter_free","siliconflow","mistral_free"}' not in text
    assert '{"openrouter_free","groq","gemini","cerebras","nvidia_nim","cohere_free","huggingface_free","siliconflow"}' in text
