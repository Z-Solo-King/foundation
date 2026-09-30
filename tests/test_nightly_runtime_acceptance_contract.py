import json
from pathlib import Path

ROOT = Path(__file__).parents[1]


def test_nightly_v3_is_dispatch_only_and_scopes_runs_by_revision():
    text = (ROOT / ".github/workflows/nightly-multi-agent-research-v3.yml").read_text(encoding="utf-8")
    assert "schedule:" not in text
    assert "workflow_dispatch:" in text
    assert "production_release_run_id" in text
    assert "nightly-multi-agent-research-" + "${{" + " inputs.target_sha || github.sha }}" in text
    assert "operations_research_ref" in text
    manifest=json.loads((Path(__file__).parents[1] / "docs" / "OPERATIONS_PIN_MANIFEST.json").read_text(encoding="utf-8"))
    assert manifest["pins"]["production_runtime"]["sha"] in text
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
    assert "_validate_chat_response" in text
    assert 'payload.get("response")' in text
    assert 'generation_status == "model_generated"' in text
    print_section = text.split("print(json.dumps", 1)[1]
    assert "raw" not in print_section


def test_runtime_probe_accepts_authenticated_nested_research_response():
    from scripts import nightly_runtime_contract_probe as probe

    payload = {
        "ok": True,
        "request_id": "nightly-contract-probe-1",
        "response": {
            "response_id": "chat-nightly-contract-probe-1",
            "provider": "cloudflare_workers_ai",
            "generation_status": "model_generated",
            "text": '{"findings":[],"follow_up_questions":[],"note":"probe"}',
        },
    }
    ok, details = probe._validate_chat_response(payload, expected_model="@cf/zai-org/glm-4.7-flash")
    assert ok is True
    assert details["provider"] == "cloudflare_workers_ai"
    assert details["response_id_present"] is True
    assert details["structured_output"] is True


def test_runtime_probe_rejects_missing_provider_or_generation_proof():
    from scripts import nightly_runtime_contract_probe as probe

    payload = {
        "ok": True,
        "response": {
            "response_id": "chat-probe",
            "generation_status": "deterministic_fallback",
            "text": '{"findings":[],"follow_up_questions":[],"note":"probe"}',
        },
    }
    ok, _details = probe._validate_chat_response(payload, expected_model="@cf/zai-org/glm-4.7-flash")
    assert ok is False