from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_production_release_dispatches_nightly_with_typed_inputs():
    workflow = (ROOT / ".github" / "workflows" / "heroic-ai-production-release.yml").read_text(encoding="utf-8")
    assert 'if [[ "$workflow" == "nightly-multi-agent-research-v3.yml" ]]; then' in workflow
    assert '--field dry_run=false' in workflow
    assert '--field target_sha="$GITHUB_SHA"' in workflow
    assert '--field production_release_run_id="$GITHUB_RUN_ID"' in workflow
    assert '--json' not in workflow
    assert 'dry_run:false' not in workflow
