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


def test_all_workflows_are_chatgpt_session_independent():
    workflow_root = ROOT / ".github/workflows"
    forbidden = ("CHATGPT", "ChatGPT", "api.openai.com", "OPENAI_API_KEY", "conversation_id", "session_id", "chat_session")
    for path in sorted(workflow_root.glob("*.yml")):
        value = path.read_text(encoding="utf-8")
        for term in forbidden:
            assert term not in value, f"{path} contains interactive-session coupling: {term}"


def test_privileged_automation_is_trusted_main_or_explicit_main_dispatch():
    privileged = (
        ROOT / ".github/workflows/autonomous-engineering-supervisor.yml",
        ROOT / ".github/workflows/project-improvement-supervisor.yml",
        ROOT / ".github/workflows/twice-daily-governance-sweep.yml",
        ROOT / ".github/workflows/commerce-feed-product-crawl.yml",
        ROOT / ".github/workflows/coverage-driven-runtime-matrix.yml",
        ROOT / ".github/workflows/live-ai-provider-crossfire.yml",
        ROOT / ".github/workflows/nightly-benchmark-ai-crossfire.yml",
        ROOT / ".github/workflows/woocommerce-emergency-xml-recovery.yml",
        ROOT / ".github/workflows/woocommerce-native-xml-recovery-v18.yml",
    )
    for path in privileged:
        value = path.read_text(encoding="utf-8")
        assert "github.ref == 'refs/heads/main'" in value, f"{path} lacks trusted-main execution guard"
        assert "pull_request:" not in value and "pull_request_target:" not in value
