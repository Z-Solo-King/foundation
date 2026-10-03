from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_family_coverage_invokes_cross_system_equivalence_gate():
    text = (ROOT / ".github/workflows/family-full-coverage.yml").read_text(
        encoding="utf-8"
    )
    assert "cross_system_equivalence.py" in text
    assert "--operations-root ../operations" in text
    assert "cross-system-equivalence.json" in text


def test_provider_crossfire_allows_up_to_six_and_records_unavailable_comparison():
    text = (ROOT / ".github/workflows/live-ai-provider-crossfire.yml").read_text(
        encoding="utf-8"
    )
    assert "--providers-max 6" in text
    assert "comparison_unavailable" in text
    assert "fewer than two configured direct providers" in text


def test_live_provider_crossfire_has_autonomous_nightly_trigger():
    text = (ROOT / ".github/workflows/live-ai-provider-crossfire.yml").read_text(
        encoding="utf-8"
    )
    assert "run-name: Live AI provider cross-fire — ${{ github.event_name }}" in text
    assert "  schedule:" in text
    assert '- cron: "30 16 * * *"' in text
    assert "  workflow_dispatch:" in text
    assert "cancel-in-progress: false" in text
    assert "CHATGPT" not in text
    assert "session_id" not in text



def test_nightly_ai_crossfire_has_six_current_parallel_models_and_truthful_gates():
    text = (ROOT / ".github/workflows/nightly-benchmark-ai-crossfire.yml").read_text(encoding="utf-8")
    expected = (
        "@cf/zai-org/glm-4.7-flash",
        "@cf/google/gemma-4-26b-a4b-it",
        "@cf/nvidia/nemotron-3-120b-a12b",
        "@cf/openai/gpt-oss-20b",
        "@cf/openai/gpt-oss-120b",
        "@cf/qwen/qwen3.8-27b",
    )
    for model in expected:
        assert model in text
    assert "max-parallel: 6" in text
    assert "CLOUDFLARE_AI_API_TOKEN" in text
    assert "python - <<'PY'" in text
    assert 'chat_template_kwargs": {"enable_thinking": False}' in text
    assert 'max_tokens": 192' in text
    assert "merge-multiple: false" in text
    assert '"expected_lane_count": 6' in text
    assert 'coverage_complete": len(rows) == 6' in text
    assert 'quality_complete": len(valid) == 6' in text
    assert 'raise SystemExit(0 if report["coverage_complete"] and report["quality_complete"] else 1)' in text
