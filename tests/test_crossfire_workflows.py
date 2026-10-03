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


def test_all_foundation_workflow_surfaces_are_chat_session_independent():
    workflow_root = ROOT / ".github/workflows"
    forbidden = (
        "CHATGPT",
        "ChatGPT",
        "api.openai.com",
        "OPENAI_API_KEY",
        "conversation_id",
        "session_id",
        "chat_session",
    )
    for path in sorted(workflow_root.glob("*.yml")):
        value = path.read_text(encoding="utf-8")
        for term in forbidden:
            assert term not in value, (
                f"{path} contains interactive-session coupling: {term}"
            )


def test_autonomous_supervisor_ids_are_run_scoped_not_interactive_session_scoped():
    value = (ROOT / "tools/autonomous_engineering_supervisor.mjs").read_text(
        encoding="utf-8"
    )
    assert "mission-${process.env.GITHUB_RUN_ID}" in value
    assert "autonomous-plan:${missionId}:${cycle}" in value
    assert "session_id" not in value
    assert "conversation_id" not in value


def test_all_registered_privileged_push_workflows_are_main_gated():
    registry = (ROOT / "docs/WORKFLOW_AUTHORITY_REGISTRY.json").read_text(
        encoding="utf-8"
    )
    data = __import__("json").loads(registry)
    for workflow_path, _role in data["explicit_privileged_workflows"]:
        path = ROOT / workflow_path
        value = path.read_text(encoding="utf-8")
        if "\n  push:" not in value and "\n'on':\n  push:" not in value:
            continue
        lines = value.splitlines()
        in_jobs = False
        i = 0
        while i < len(lines):
            if lines[i] == "jobs:":
                in_jobs = True
                i += 1
                continue
            if not in_jobs:
                i += 1
                continue
            if (
                lines[i].startswith("  ")
                and not lines[i].startswith("    ")
                and lines[i].rstrip().endswith(":")
            ):
                start = i
                i += 1
                while i < len(lines) and not (
                    lines[i].startswith("  ")
                    and not lines[i].startswith("    ")
                    and lines[i].rstrip().endswith(":")
                ):
                    i += 1
                block = lines[start:i]
                if any(line.startswith("    runs-on:") for line in block):
                    assert any(
                        line.startswith("    if:")
                        and "github.ref == 'refs/heads/main'" in line
                        for line in block
                    ), f"{workflow_path} has a privileged push job without a main guard"
                continue
            i += 1
