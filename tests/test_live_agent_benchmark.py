import re
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def test_live_agent_runner_is_private_bridge():
    source=(ROOT/"benchmark/multi_agent/live_agent_benchmark.py").read_text(encoding="utf-8")
    assert "OPERATIONS_AGENT_BENCHMARK_RUNNER" in source
    assert "provider" not in source.lower()
    assert "ROLE_INSTRUCTIONS" not in source
    assert "DEFAULT_MODELS" not in source


def test_live_agent_workflow_uses_private_operations_runtime():
    source=(ROOT/".github/workflows/live-ai-agent-benchmark.yml").read_text(encoding="utf-8")
    assert "actions/create-github-app-token@bcd2ba49218906704ab6c1aa796996da409d3eb1" in source
    assert "operations-agent-benchmark" in source
    assert "ai_agent_private_task_matrix_v1.json" in source


def test_public_crossfire_runner_contains_no_provider_endpoint_or_secret_inventory():
    source=(ROOT/"benchmark/ai_provider_crossfire.py").read_text(encoding="utf-8")
    forbidden=("api.groq.com","generativelanguage.googleapis.com","PROVIDER_KEYS_JSON","GROQ_API_KEY","GEMINI_API_KEY","NVIDIA_NIM_API_KEY","HF_TOKEN","openrouter.ai/api/v1")
    assert not any(token in source for token in forbidden)
