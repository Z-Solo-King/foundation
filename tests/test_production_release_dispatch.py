from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_production_release_dispatches_nightly_with_json_on_stdin():
    workflow = (ROOT / ".github" / "workflows" / "heroic-ai-production-release.yml").read_text(encoding="utf-8")
    assert 'jq -nc --arg target_sha "$GITHUB_SHA" --arg production_release_run_id "$GITHUB_RUN_ID"' in workflow
    assert '| gh workflow run "$workflow" --repo "$GITHUB_REPOSITORY" --ref main --json &' in workflow
    assert 'gh workflow run "$workflow" --repo "$GITHUB_REPOSITORY" --ref main \\\n              jq -nc' not in workflow
