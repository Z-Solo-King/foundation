    auxiliary = {
        "live-chatbot-production-smoke.yml": expected_production,
        "coverage-driven-runtime-matrix.yml": expected_nightly,
        "polyglot-governance-audit.yml": expected_nightly,
        "live-nightly-research-canary.yml": expected_nightly,
        "nightly-research-provider-preflight.yml": expected_nightly,
    }
    for filename, expected in auxiliary.items():
        workflow = (WORKFLOW_ROOT / filename).read_text(encoding="utf-8")
        if filename == "polyglot-governance-audit.yml":
            assert "docs/OPERATIONS_PIN_MANIFEST.json" in workflow
            assert "production_runtime" in workflow
            assert 'default: ""' in workflow
        else:
            assert expected in workflow
        assert "50e642dfb05846963a82fe76f4f5fe085d4b9a8c" not in workflow
def test_github_app_token_inputs_use_client_id():
    for name, text in _workflow_texts().items():
        if "actions/create-github-app-token@" in text:
            assert "app-id: $" + "{{ secrets.OPERATIONS_APP_ID }}" not in text, name
            assert "client-id: $" + "{{ secrets.OPERATIONS_APP_ID }}" in text, name
def test_live_extractor_benchmark_normalizes_case_receipts_before_upload():
    workflow = _workflow_texts()["live-extractor-benchmark.yml"]