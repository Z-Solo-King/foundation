import json
from pathlib import Path

from benchmark.multi_agent.live_agent_benchmark import DEFAULT_MODELS, DEFAULT_ROLES, build_prompt, canonical_digest


def test_runner_defines_full_model_and_role_matrix():
    assert DEFAULT_MODELS == [
        "@cf/zai-org/glm-4.7-flash",
        "@cf/google/gemma-4-26b-a4b-it",
    ]
    assert DEFAULT_ROLES == ["main", "explorer", "worker", "researcher", "advisor"]


def test_prompt_is_project_native_without_hidden_reasoning():
    matrix = json.loads(Path("benchmark/ai_agent_task_matrix_v1.json").read_text(encoding="utf-8"))
    prompt = build_prompt(matrix["tasks"][0], "main", 1)
    assert matrix["tasks"][0]["task_id"] in prompt
    assert "no hidden-chain-of-thought disclosure" in prompt
    assert "Return a concise JSON object" in prompt


def test_digest_is_deterministic():
    assert canonical_digest({"b": 2, "a": 1}) == canonical_digest({"a": 1, "b": 2})
