from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_live_agent_public_surface_is_only_a_private_runtime_bridge():
    source = (ROOT / "benchmark/multi_agent/live_agent_benchmark.py").read_text(encoding="utf-8")
    assert "OPERATIONS_AGENT_BENCHMARK_RUNNER" in source
    assert "DEFAULT_MODELS" not in source
    assert "ROLE_INSTRUCTIONS" not in source
    assert "call_model" not in source


def test_live_agent_workflow_uses_private_operations_runtime():
    source = (ROOT / ".github/workflows/live-ai-agent-benchmark.yml").read_text(encoding="utf-8")
    assert "actions/create-github-app-token@bcd2ba49218906704ab6c1aa796996da409d3eb1" in source
    assert "permission-contents: read" in source
    assert "operations-agent-benchmark" in source
    assert "ai_agent_private_task_matrix_v1.json" in source
    assert "persist-credentials: false" in source


def test_provider_crossfire_public_surface_is_only_a_private_runtime_bridge():
    source = (ROOT / "benchmark/ai_provider_crossfire.py").read_text(encoding="utf-8")
    assert "OPERATIONS_CROSSFIRE_RUNNER" in source
    assert "PROVIDER_KEYS_JSON" not in source
    assert "api.groq.com" not in source
    assert "generativelanguage.googleapis.com" not in source
