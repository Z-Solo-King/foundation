from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_production_release_dispatches_nightly_with_typed_inputs():
    workflow = (ROOT / ".github" / "workflows" / "heroic-ai-production-release.yml").read_text(encoding="utf-8")
    assert "Preflight exact nightly runtime before research dispatch" in workflow
    assert "gh workflow run nightly-research-provider-preflight.yml" in workflow
    assert '--field dry_run=false' in workflow
    assert '--field target_sha="$GITHUB_SHA"' in workflow
    assert '--field production_release_run_id="$GITHUB_RUN_ID"' in workflow
    assert 'gh workflow run nightly-research-provider-preflight.yml' in workflow
    assert 'preflight_run_id' in workflow
    assert 'dry_run:false' not in workflow
