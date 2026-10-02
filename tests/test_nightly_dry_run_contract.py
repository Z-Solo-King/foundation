from pathlib import Path


ROOT = Path(__file__).parents[1] / ".github" / "workflows"


def test_nightly_dry_run_skips_live_only_runtime_probe_and_keeps_mode_for_crossfire():
    text = (ROOT / "nightly-multi-agent-research-v3.yml").read_text(encoding="utf-8")
    probe_start = text.index("      - name: Verify exact deployed research runtime")
    probe_end = text.index("      - name: Authenticate private research source", probe_start)
    probe_block = text[probe_start:probe_end]
    assert "if: ${{ inputs.dry_run != true }}" in probe_block
    assert "node scripts/nightly_runtime_contract_probe.mjs" in probe_block
    mode_start = text.index("      - name: Research mode")
    validate_start = text.index("      - name: Validate pinned Operations research contract")
    assert mode_start < validate_start
    crossfire_block = text[
        text.index("      - name: Run complete crossfire research") : text.index(
            "      - name: Materialize and validate lane artifacts"
        )
    ]
    assert "args+=(--dry-run)" in crossfire_block
