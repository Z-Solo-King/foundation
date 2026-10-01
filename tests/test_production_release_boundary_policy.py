from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
PRODUCTION_SCRIPT = ROOT / "scripts" / "production_release.sh"

def test_production_release_defines_git_askpass_path():
    text = PRODUCTION_SCRIPT.read_text(encoding="utf-8")
    assert 'askpass="$RUNNER_TEMP/git-askpass-operations.sh"' in text
    assert '\\n\\n\\naskpass=' not in text

def test_production_release_compiles_pinned_operations_before_deploy():
    text = PRODUCTION_SCRIPT.read_text(encoding="utf-8")
    assert 'python -m compileall -q "$RUNNER_TEMP/operations"' in text
    assert 'echo "Pinned Operations compile: PASS"' in text

def test_production_release_overlays_current_operations_navigation():
    text = PRODUCTION_SCRIPT.read_text(encoding="utf-8")
    assert 'git -C "$RUNNER_TEMP/operations" show "origin/main:docs/FAMILY_SYNC_STATE.json" > "$RUNNER_TEMP/operations/docs/FAMILY_SYNC_STATE.json"' in text
    assert 'git -C "$RUNNER_TEMP/operations" show "origin/main:docs/AI_ANALYSIS_MAP.md" > "$RUNNER_TEMP/operations/docs/AI_ANALYSIS_MAP.md"' in text

def test_d1_migration_config_uses_resolved_database_values():
    text = PRODUCTION_SCRIPT.read_text(encoding="utf-8")
    assert '"database_name = \\"${database_name}\\""' in text
    assert '"database_id = \\"${database_id}\\""' in text
    assert '"database_name = \\"\\${database_name}\\""' not in text
    assert '"database_id = \\"\\${database_id}\\""' not in text
def test_production_release_shell_syntax_is_valid():
    result = subprocess.run(["bash", "-n", str(PRODUCTION_SCRIPT)], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr

def test_production_release_uses_migrations_once_and_does_not_reexecute_raw_d1_schema():
    text = PRODUCTION_SCRIPT.read_text(encoding="utf-8")
    assert text.count("RESOURCE_GOVERNANCE_D1_SCHEMA.sql") == 0
    assert text.count('d1 migrations apply "$database_name" --remote') == 1
    assert 'D1_MIGRATIONS_FINGERPRINT=' in text
    assert 'current_d1_migrations_fingerprint=' in text
    assert 'sha256sum "$file" | awk' in text
    assert 'migration content fingerprint matches last live-verified production schema' in text
    assert 'migration content fingerprint differs from last live-verified production schema' in text
    assert 'current-heroic-core-settings.json' not in text
    assert 'RELEASE_OPERATIONS_REF' in text
    assert 'current_operations_ref=' not in text
    assert 'd1 execute "$database_name" --remote' not in text
    assert text.count('foundation-binding-${ACCEPTANCE_RUN_ID}') == 1
    assert text.count('persistence-boundary-${ACCEPTANCE_RUN_ID}') == 1
    assert 'persistence_bootstrap_deferred' not in text
    assert text.count('echo "Production release completed for ${GITHUB_SHA}"') == 1

def test_persistence_rollover_verification_is_single_use_in_release_script():
    text = PRODUCTION_SCRIPT.read_text(encoding='utf-8')
    assert text.count('persistence_verify_status=$(curl -sS --max-time 30') == 1
    assert text.count('echo "POST persistence_verify -> HTTP') == 1
    assert text.count('memory_persisted_across_version == true') == 1

def test_required_pr_boundary_scan_does_not_ban_abstract_operations_binding():
    workflow = (ROOT / ".github" / "workflows" / "required-pr-checks.yml").read_text(encoding="utf-8")
    assert "! grep -RniE 'operations|" not in workflow
    assert "extractor_mapper|private.chatbot|resource_ledger|promotion.py|trust_boundary|CONTROL_PLANE" in workflow


def test_production_boundary_scan_matches_public_worker_architecture():
    text = (ROOT / "scripts/production_release.sh").read_text(encoding="utf-8")

    assert "! grep -RniE 'operations|extractor_mapper" not in text
    assert "! grep -RniE 'extractor_mapper|private\\.chatbot|resource_ledger|promotion\\.py|trust_boundary|CONTROL_PLANE' foundation_core backend wrangler.toml migrations" in text
    assert "! grep -nE 'extractor_mapper|private\\.chatbot|resource_ledger|promotion\\.py|trust_boundary|CONTROL_PLANE' worker.py edge.ts" in text

def test_operations_binding_is_generated_but_private_service_name_stays_out_of_worker():
    text = (ROOT / "scripts/production_release.sh").read_text(encoding="utf-8")
    worker = (ROOT / "worker.py").read_text(encoding="utf-8")

    assert 'OPERATIONS_SERVICE_NAME="operations"' in text
    assert 'binding = "OPERATIONS"' in text
    assert "research-intelligence-engine-private" not in worker

def test_production_release_does_not_hardcode_private_d1_name():
    text = PRODUCTION_SCRIPT.read_text(encoding="utf-8")
    assert "research-intelligence" not in text
    assert 'database_name="$(sed -n' in text
    assert 'select(.name == $expected_name)' in text
    assert 'database_name = \\"${database_name}\\"' in text

def test_production_health_check_requires_production_environment():
    text = (ROOT / "scripts/production_release.sh").read_text(encoding="utf-8")
    assert '.ok == true and .environment == "production"' in text

def test_release_d1_config_is_passed_as_wrangler_global_option():
    text = PRODUCTION_SCRIPT.read_text(encoding="utf-8")
    assert 'wrangler@4.131.1 --config "$d1_migrations_config" d1 migrations apply "$database_name" --remote' in text
    assert 'd1 execute "$database_name" --remote' not in text
    assert 'wrangler@4.131.1 d1 migrations apply "$database_name" --remote --config "$d1_migrations_config"' not in text

def test_release_d1_commands_use_dedicated_d1_config():
    text = PRODUCTION_SCRIPT.read_text(encoding="utf-8")
    assert 'd1_migrations_config="$GITHUB_WORKSPACE/wrangler.d1.migrations.generated.toml"' in text
    assert 'd1 migrations apply "$database_name" --remote' in text
    assert 'd1 execute "$database_name" --remote' not in text
    assert '--config="$RUNNER_TEMP/operations/wrangler.toml"' not in text

def test_d1_migration_config_pins_repository_migrations_dir():
    text = PRODUCTION_SCRIPT.read_text(encoding="utf-8")
    assert 'migrations_dir = "migrations"' in text


def test_release_d1_commands_do_not_repeat_global_config_flag():
    text = PRODUCTION_SCRIPT.read_text(encoding="utf-8")
    for line in text.splitlines():
        if 'd1 execute "$database_name" --remote' in line:
            continue
    assert '  --config="$d1_migrations_config"' not in text

def test_reciprocal_service_bindings_use_binding_free_bootstrap():
    text = (ROOT / "scripts/production_release.sh").read_text(encoding="utf-8")
    assert "Operations binding-free bootstrap deployment: PASS" in text
    assert 'bootstrap_config="$RUNNER_TEMP/operations/wrangler.bootstrap.toml"' in text
    assert '[[services]]' in text
    assert '(cd "$RUNNER_TEMP/operations" && pywrangler deploy --config "$bootstrap_config"' in text
    assert text.count('(cd "$RUNNER_TEMP/operations" && pywrangler deploy --config "$bootstrap_config"') == 1
    assert '/workers/scripts/${OPERATIONS_SERVICE_NAME}/settings' not in text

def test_operations_bootstrap_config_lives_with_entrypoint_checkout():
    text = (ROOT / "scripts/production_release.sh").read_text(encoding="utf-8")
    assert 'bootstrap_config="$RUNNER_TEMP/operations/wrangler.bootstrap.toml"' in text
    assert 'cp "$RUNNER_TEMP/operations/wrangler.toml" "$bootstrap_config"' in text
    assert '(cd "$RUNNER_TEMP/operations" && pywrangler deploy --config "$bootstrap_config"' in text