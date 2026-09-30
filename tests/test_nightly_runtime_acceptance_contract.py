from pathlib import Path

ROOT = Path(__file__).parents[1]


def test_nightly_v3_keeps_schedule_but_scopes_runs_by_revision():
    text = (ROOT / ".github/workflows/nightly-multi-agent-research-v3.yml").read_text(encoding="utf-8")
    assert 'cron: "30 19 * * *"' in text
    assert "nightly-multi-agent-research-" + "${{" + " inputs.target_sha || github.sha }}" in text
    assert "operations_research_ref" in text
    assert "05bb78285cb3d42c0b90a9975bb28121895dfe53" in text
    assert "Verify exact deployed research runtime" in text
    assert "nightly_runtime_contract_probe.py" in text


def test_provider_preflight_uses_same_exact_probe():
    text = (ROOT / ".github/workflows/nightly-research-provider-preflight.yml").read_text(encoding="utf-8")
    assert "workflow_dispatch:" in text
    assert "operations_research_ref" in text
    assert "nightly_runtime_contract_probe.py" in text
    assert "X-Heroic-Research-Proof" not in text
    assert "api/v1/chat" not in text


def test_release_waits_for_preflight_before_nightly():
    text = (ROOT / ".github/workflows/heroic-ai-production-release.yml").read_text(encoding="utf-8")
    assert "Preflight exact nightly runtime before research dispatch" in text
    assert "gh workflow run nightly-research-provider-preflight.yml" in text
    assert "Research preflight failed; refusing to launch nightly." in text
    assert "gh workflow run nightly-multi-agent-research-v3.yml" in text


def test_runtime_probe_does_not_print_response_body_or_token():
    text = (ROOT / "scripts/nightly_runtime_contract_probe.py").read_text(encoding="utf-8")
    assert "AUTH_TOKEN" not in text
    assert 'payload.get("choices"' in text
    print_section = text.split("print(json.dumps", 1)[1]
    assert "raw" not in print_section
