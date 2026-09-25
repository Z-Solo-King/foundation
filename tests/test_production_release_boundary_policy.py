from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_production_boundary_scan_matches_public_worker_architecture():
    text = (ROOT / "scripts/production_release.sh").read_text(encoding="utf-8")

    assert "! grep -RniE 'operations|extractor_mapper" not in text
    assert "! grep -RniE 'extractor_mapper|private\\.chatbot|resource_ledger|promotion\\.py|trust_boundary|CONTROL_PLANE' foundation_core backend wrangler.toml migrations" in text
    assert "! grep -nE 'extractor_mapper|private\\.chatbot|resource_ledger|promotion\\.py|trust_boundary|CONTROL_PLANE' worker.py" in text


def test_operations_binding_is_generated_but_private_service_name_stays_out_of_worker():
    text = (ROOT / "scripts/production_release.sh").read_text(encoding="utf-8")
    worker = (ROOT / "worker.py").read_text(encoding="utf-8")

    assert 'OPERATIONS_SERVICE_NAME="operations"' in text
    assert 'binding = "OPERATIONS"' in text
    assert "research-intelligence-engine-private" not in worker


def test_production_health_check_requires_production_environment():
    text = (ROOT / "scripts/production_release.sh").read_text(encoding="utf-8")
    assert '.ok == true and .environment == "production"' in text


def test_reciprocal_service_bindings_use_binding_free_bootstrap():
    text = (ROOT / "scripts/production_release.sh").read_text(encoding="utf-8")
    assert "Operations binding-free bootstrap deployment: PASS" in text
    assert 'bootstrap_config="$RUNNER_TEMP/operations/wrangler.bootstrap.toml"' in text
    assert '[[services]]' in text
    assert 'pywrangler deploy --config "$bootstrap_config"' in text
    assert '/workers/scripts/${OPERATIONS_SERVICE_NAME}/settings' not in text


def test_operations_bootstrap_config_lives_with_entrypoint_checkout():
    text = (ROOT / "scripts/production_release.sh").read_text(encoding="utf-8")
    assert 'bootstrap_config="$RUNNER_TEMP/operations/wrangler.bootstrap.toml"' in text
    assert 'cp "$RUNNER_TEMP/operations/wrangler.toml" "$bootstrap_config"' in text
    assert '(cd "$RUNNER_TEMP/operations" && pywrangler deploy --config "$bootstrap_config"' in text


def test_production_uses_free_workers_dev_origin_without_custom_zone_preflight():
    text = (ROOT / "scripts/production_release.sh").read_text(encoding="utf-8")
    assert 'BASE_URL="https://heroic.ai.workers.dev"' in text
    assert 'workers_dev = true' in text
    assert 'name = "heroic"' in text
    assert 'zones?name=heroic-ai.dev&status=active' not in text
