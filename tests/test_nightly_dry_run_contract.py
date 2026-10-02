from pathlib import Path

ROOT = Path(__file__).parents[1] / ".github" / "workflows"


def test_nightly_dry_run_selects_mode_before_live_only_runtime_probe():
    text = (ROOT / "nightly-multi-agent-research-v3.yml").read_text(encoding="utf-8")
    mode_start = text.index("      - name: Research mode")
    probe_start = text.index("      - name: Verify exact deployed research runtime")
    assert mode_start < probe_start
    probe_block = text[
        probe_start : text.index(
            "      - name: Authenticate private research source", probe_start
        )
    ]
    assert 'if [[ "${{ steps.mode.outputs.mode }}" != "live" ]]; then' in probe_block
    assert "node scripts/nightly_runtime_contract_probe.mjs" in probe_block
    crossfire_block = text[
        text.index("      - name: Run complete crossfire research") : text.index(
            "      - name: Materialize and validate lane artifacts"
        )
    ]
    assert "args+=(--dry-run)" in crossfire_block
