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
    assert "Enforce comparative benchmark availability" in text
    assert "path: operations-provider-benchmark" in text
    assert "${{ runner.temp }}/operations-provider-benchmark" not in text
    assert (
        "${{ github.workspace }}/operations-provider-benchmark/private/benchmark/ai_provider_crossfire.py"
        in text
    )
    assert (
        "PYTHONPATH: ${{ github.workspace }}:${{ github.workspace }}/operations-provider-benchmark"
        in text
    )
    assert "GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}" in text
    assert "GROQ_API_KEY: ${{ secrets.GROQ_API_KEY }}" in text
    assert "CEREBRAS_API_KEY: ${{ secrets.CEREBRAS_API_KEY }}" in text
    assert "NVIDIA_NIM_API_KEY: ${{ secrets.NVIDIA_NIM_API_KEY }}" in text
    assert "COHERE_API_KEY: ${{ secrets.COHERE_API_KEY }}" in text
    assert "OPENROUTER_API_KEY: ${{ secrets.OPENROUTER_API_KEY }}" in text
    assert "HF_TOKEN: ${{ secrets.HF_TOKEN }}" in text
    assert "SILICONFLOW_API_KEY: ${{ secrets.SILICONFLOW_API_KEY }}" in text


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