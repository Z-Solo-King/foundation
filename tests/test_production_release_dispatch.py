from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_production_release_dispatches_nightly_with_typed_inputs():
    workflow = (ROOT / ".github" / "workflows" / "heroic-ai-production-release.yml").read_text(encoding="utf-8")
    assert 'gh workflow run "$workflow" --repo "$GITHUB_REPOSITORY" --ref main \
                --field dry_run=false \
                --field target_sha="$GITHUB_SHA" \
                --field production_release_run_id="$GITHUB_RUN_ID" &' in workflow
    assert '--json' not in workflow
    assert 'dry_run:false' not in workflow
