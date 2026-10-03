from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_family_coverage_invokes_cross_system_equivalence_gate():
    text = (ROOT / ".github/workflows/family-full-coverage.yml").read_text(
        encoding="utf-8"
    )
    assert "cross_system_equivalence.py" in text
    assert "--operations-root ../operations" in text
    assert "cross-system-equivalence.json" in text


def test_provider_crossfire_common_workflow_owns_provider_execution():
    text = (ROOT / ".github/workflows/chatbot-post-release-crossfire.yml").read_text(
        encoding="utf-8"
    )
    assert "workflow_call:" in text
    assert "--providers-max 6" in text
    assert "comparison_unavailable" in text
    assert "fewer than two configured direct providers" in text
    assert 'python-version: "3.14"' in text
    assert "Install pinned Operations runtime" in text
    assert "pip install --disable-pip-version-check -e ." in text


def test_live_provider_crossfire_is_a_thin_reusable_workflow_caller():
    text = (ROOT / ".github/workflows/live-ai-provider-crossfire.yml").read_text(
        encoding="utf-8"
    )
    assert "run-name: Live AI provider cross-fire — ${{ github.event_name }}" in text
    assert "  schedule:" in text
    assert '- cron: "30 16 * * *"' in text
    assert "  workflow_dispatch:" in text
    assert "jobs:" in text
    assert "uses: ./.github/workflows/chatbot-post-release-crossfire.yml" in text
    assert "secrets: inherit" in text
    assert "steps:" not in text
    assert "--providers-max 6" not in text
    assert "actions/create-github-app-token" not in text
    assert "private/benchmark/ai_provider_crossfire.py" not in text


def test_nightly_ai_crossfire_uses_canonical_worker_boundary_and_truthful_gates():
    text = (ROOT / ".github/workflows/nightly-benchmark-ai-crossfire.yml").read_text(
        encoding="utf-8"
    )
    assert "PUBLIC_WORKER_URL: https://heroic-ai.pages.dev" in text
    assert "AUTH_TOKEN: ${{ secrets.AUTH_TOKEN }}" in text
    assert "CLOUDFLARE_API_TOKEN" not in text
    assert "CLOUDFLARE_ACCOUNT_ID" not in text
    assert "/api/v1/benchmark/ai-crossfire" in text
    assert "nightly-benchmark-ai-crossfire-request/v2" in text
    assert "nightly-benchmark-ai-crossfire-result/v2" in text
    assert "Resolve expected Operations production pin" in text
    assert "expected_operations_ref" in text
    assert "model_count_expected" in text
    assert "model_count_observed" in text
    assert "quality_complete" in text
    assert "coverage_complete" in text
    assert "python - <<'PY'" in text
    assert "max-parallel: 6" not in text


def test_nightly_ai_crossfire_validates_manual_run_provenance():
    text = (ROOT / ".github/workflows/nightly-benchmark-ai-crossfire.yml").read_text(
        encoding="utf-8"
    )
    assert (
        'gh run view "$RUN_ID" --repo "$GITHUB_REPOSITORY" --json name,status,conclusion,headSha,headBranch,event'
        in text
    )
    assert '.status == "completed"' in text
    assert '.conclusion == "success"' in text
    assert "jq -e" in text
    assert (
        'gh run list --workflow autonomous-benchmark.yml --repo "$GITHUB_REPOSITORY" --branch main'
        in text
    )
    assert '.headBranch == "main"' in text
    assert "operations_ref" in text
    assert 'response.get("operations_ref")' in text


def test_nightly_ai_crossfire_keeps_production_pin_guard_in_request_path():
    text = (ROOT / ".github/workflows/nightly-benchmark-ai-crossfire.yml").read_text(
        encoding="utf-8"
    )
    assert "EXPECTED_OPERATIONS_REF" in text
    assert '"expected_operations_ref": os.environ["EXPECTED_OPERATIONS_REF"]' in text
    assert (
        'response.get("operations_ref") != os.environ["EXPECTED_OPERATIONS_REF"]'
        in text
    )

def test_common_provider_crossfire_accepts_manual_and_reusable_inputs():
    text = (ROOT / ".github/workflows/chatbot-post-release-crossfire.yml").read_text(
        encoding="utf-8"
    )
    assert "workflow_call:" in text
    assert "workflow_dispatch:" in text
    assert "operations_ref:" in text
    assert "OPERATIONS_APP_ID:" in text
    assert "OPERATIONS_APP_PRIVATE_KEY:" in text
    assert "OPENROUTER_API_KEY:" in text
    assert "SILICONFLOW_API_KEY:" in text
    assert "cancel-in-progress: false" in text
