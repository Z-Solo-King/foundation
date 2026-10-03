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


def test_ai_automation_is_chatgpt_session_independent():
    workflow_paths = (
        ROOT / ".github/workflows/autonomous-benchmark.yml",
        ROOT / ".github/workflows/nightly-benchmark-ai-crossfire.yml",
        ROOT / ".github/workflows/live-ai-provider-crossfire.yml",
        ROOT / ".github/workflows/autonomous-engineering-supervisor.yml",
        ROOT / ".github/workflows/project-improvement-supervisor.yml",
        ROOT / ".github/workflows/twice-daily-governance-sweep.yml",
    )
    forbidden = ("CHATGPT", "ChatGPT", "api.openai.com", "OPENAI_API_KEY", "conversation_id", "session_id", "chat_session")
    for path in workflow_paths:
        value = path.read_text(encoding="utf-8")
        for term in forbidden:
            assert term not in value, f"{path} contains ChatGPT/session coupling: {term}"


def test_ai_benchmark_crossfire_has_only_independent_trusted_triggers():
    value = (ROOT / ".github/workflows/nightly-benchmark-ai-crossfire.yml").read_text(encoding="utf-8")
    trigger_block = value.split("permissions:", 1)[0]
    assert '    - cron: "0 17 * * *"' in trigger_block
    assert "  workflow_dispatch:" in trigger_block
    for forbidden in ("workflow_run:", "repository_dispatch:", "pull_request:", "pull_request_target:", "merge_group:"):
        assert forbidden not in trigger_block
    assert "github.ref == 'refs/heads/main'" in value
    assert "--status completed" in value
    assert '.headBranch == "main"' in value
    assert '.databaseId == ($id|tonumber)' in value
    assert ".repository_revision == $source_sha" in value


def test_privileged_provider_crossfire_is_trusted_main_only_for_privileged_execution():
    value = (ROOT / ".github/workflows/live-ai-provider-crossfire.yml").read_text(encoding="utf-8")
    trigger_block = value.split("permissions:", 1)[0]
    assert "  schedule:" in trigger_block
    assert "  workflow_dispatch:" in trigger_block
    assert "pull_request:" not in trigger_block
    assert "pull_request_target:" not in trigger_block
    assert "github.ref == 'refs/heads/main'" in value
    assert "path: operations-provider-benchmark" in value
    assert "OPERATIONS_CROSSFIRE_RUNNER: ${{ github.workspace }}/operations-provider-benchmark/" in value


def test_active_automation_uses_canonical_public_front_door():
    paths = (
        ROOT / ".github/workflows/autonomous-engineering-supervisor.yml",
        ROOT / ".github/workflows/project-improvement-supervisor.yml",
        ROOT / ".github/workflows/twice-daily-governance-sweep.yml",
        ROOT / ".github/workflows/commerce-feed-product-crawl.yml",
        ROOT / ".github/workflows/coverage-driven-runtime-matrix.yml",
        ROOT / ".github/workflows/woocommerce-emergency-xml-recovery.yml",
        ROOT / ".github/workflows/woocommerce-native-xml-recovery-v18.yml",
        ROOT / "tools/autonomous_engineering_supervisor.mjs",
    )
    for path in paths:
        value = path.read_text(encoding="utf-8")
        assert "ai-cio.pages.dev" not in value
        assert "heroic-ai.pages.dev" in value


def test_all_foundation_workflow_surfaces_are_chat_session_independent():
    workflow_root = ROOT / ".github/workflows"
    forbidden = ("CHATGPT", "ChatGPT", "api.openai.com", "OPENAI_API_KEY", "conversation_id", "session_id", "chat_session")
    for path in sorted(workflow_root.glob("*.yml")):
        value = path.read_text(encoding="utf-8")
        for term in forbidden:
            assert term not in value, f"{path} contains interactive-session coupling: {term}"


def test_autonomous_supervisor_ids_are_run_scoped_not_interactive_session_scoped():
    value = (ROOT / "tools/autonomous_engineering_supervisor.mjs").read_text(encoding="utf-8")
    assert "mission-${process.env.GITHUB_RUN_ID}" in value
    assert "request_id: `autonomous-plan:${missionId}:${cycle}`" in value
    assert "session_id" not in value
    assert "conversation_id" not in value
