from __future__ import annotations

import json
import pathlib


ROOT = pathlib.Path(__file__).parents[1] / ".github" / "workflows"


def test_fresh_nightly_identity_is_dispatchable_and_uses_current_operations():
    text = (ROOT / "nightly-multi-agent-research-v3.yml").read_text(encoding="utf-8")
    assert "workflow_dispatch:" in text
    assert "schedule:" not in text
    assert "production_release_run_id" in text
    assert "OPERATIONS_REPOSITORY: Z-Solo-King/operations" in text
    assert "OPERATIONS_RESEARCH_REF:" in text
    manifest = json.loads(
        (
            pathlib.Path(__file__).parents[1]
            / "docs"
            / "OPERATIONS_PIN_MANIFEST.json"
        ).read_text(encoding="utf-8")
    )
    assert manifest["pins"]["research_runtime"]["sha"] in text
    assert "private.multi_agent.runner" in text
    assert "private.multi_agent.project_research" in text


def test_fresh_bridge_identity_is_dispatchable_and_bounded():
    text = (ROOT / "foundation-canonical-workflow-bridge-v3.yml").read_text(
        encoding="utf-8"
    )
    assert "workflow_dispatch:" in text
    assert "main-push-actions-control-plane-probe-v2.yml" in text
    assert "nightly-multi-agent-research-v3.yml" in text
    assert "workflow-dispatch-bridge-receipt/v2" in text
    assert "actions/upload-artifact@" in text


def test_fresh_acceptance_workflow_dispatches_both_identities():
    text = (ROOT / "fresh-control-plane-identity-acceptance.yml").read_text(
        encoding="utf-8"
    )
    assert "gh workflow run foundation-canonical-workflow-bridge-v3.yml" in text
    assert "gh workflow run nightly-multi-agent-research-v3.yml" in text
    assert "-f dry_run=true" in text
    assert "jobs?per_page=100" in text
    assert (
        'jobs_status="$(curl -sS -o "$RUNNER_TEMP/bridge-jobs.json" -w \'%{http_code}\''
        in text
    )
    assert (
        'jobs_status="$(curl -sS -o "$RUNNER_TEMP/nightly-jobs.json" -w \'%{http_code}\''
        in text
    )
    assert "404) jobs=0" in text
    assert "Unexpected bridge jobs HTTP status" in text
    assert "Unexpected nightly jobs HTTP status" in text

def test_nightly_dry_run_selects_mode_before_live_only_runtime_probe():
    text = (ROOT / "nightly-multi-agent-research-v3.yml").read_text(encoding="utf-8")
    mode_start = text.index("      - name: Research mode")
    probe_start = text.index("      - name: Verify exact deployed research runtime")
    assert mode_start < probe_start
    probe_block = text[
        probe_start : text.index("      - name: Authenticate private research source", probe_start)
    ]
    assert "if: ${{ steps.mode.outputs.mode == 'live' }}" in probe_block
    assert "node scripts/nightly_runtime_contract_probe.mjs" in probe_block
    crossfire_block = text[
        text.index("      - name: Run complete crossfire research") : text.index(
            "      - name: Materialize and validate lane artifacts"
        )
    ]
    assert "args+=(--dry-run)" in crossfire_block
