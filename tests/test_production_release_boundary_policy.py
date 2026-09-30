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

def test_d1_migration_fingerprint_matches_repository_bytes():
    import hashlib
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    entries = []
    for path in sorted(root.joinpath("migrations").glob("*.sql")):
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        entries.append(f"{path.name}\t{digest}\n")
    expected = hashlib.sha256("".join(entries).encode("utf-8")).hexdigest()
    text = PRODUCTION_SCRIPT.read_text(encoding="utf-8")
    assert f'D1_MIGRATIONS_FINGERPRINT="{expected}"' in text


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

def test_production_uses_pages_front_door_with_private_backend_boundary():
    text = (ROOT / "scripts/production_release.sh").read_text(encoding="utf-8")
    assert 'BASE_URL=' in text and 'ai-cio.pages.dev' in text
    assert 'workers_dev = false' in text
    assert 'name = "heroic"' in text
    assert '! grep -q \'^service = "heroic"$\' "$bootstrap_config"' in text
    assert 'settings_worker="${PYTHON_CORE_WORKER_NAME}"' in text
    assert 'B2_BUCKET' in text and 'B2_ENDPOINT' in text
    assert 'settings_worker="${PYTHON_CORE_WORKER_NAME}"' in text
    assert 'settings_worker="${PUBLIC_WORKER_NAME}"' in text
    assert 'settings_status=$(curl -sS -o "$settings_path" -w \'%{http_code}\'' in text
    assert 'workers/scripts/heroic/subdomain' in text
    assert 'pages/projects/ai' not in text
    assert 'Canonical Pages front door check failed' in text
    assert 'BASE_URL/health' in text
    assert 'workers/scripts/foundation' in text
    assert 'ai-cio.pages.dev' in text



# The diagnostic payload may flatten runtime checks or nest them; the release contract accepts both shapes.
def test_infrastructure_diagnostic_failure_reports_only_failed_check_names():
    text = PRODUCTION_SCRIPT.read_text(encoding="utf-8")
    assert 'Authenticated infrastructure diagnostic acceptance: FAIL' in text
    assert 'failed_checks="$(jq -r' in text
    assert 'select((.name? | type) == "string" and (.ok? | type) == "boolean" and .ok != true)' in text
    assert 'def named_checks:' in text
    assert '[.. | objects | select((.name? | type) == "string" and (.ok? | type) == "boolean")]' in text
    assert 'cat diagnostic.json' not in text
    assert '.. | objects' in text
    assert 'select((.name? | type) == "string" and (.ok? | type) == "boolean" and .ok != true)' in text

def test_live_chat_provider_provenance_uses_authenticated_proof_projection():
    text = PRODUCTION_SCRIPT.read_text(encoding="utf-8")
    assert 'X-Heroic-Research-Proof: 1' in text
    assert '.response.provider == "cloudflare_workers_ai"' in text
    assert 'live_chat_provider=$(jq -r' in text
    assert 'resource_governance_reservations' not in text
    assert 'd1 execute "$database_name" --remote' not in text


def test_chat_auth_boundary_checks_canonical_module():
    text = PRODUCTION_SCRIPT.read_text(encoding="utf-8")
    assert 'grep -q \'CHAT_BACKEND_TOKEN\' "$RUNNER_TEMP/operations/private/chat_auth.py"' in text
    assert 'grep -q \'from private.chat_auth import authorized_chat_request\' "$RUNNER_TEMP/operations/worker.py"' in text
    assert 'CHAT_BACKEND_TOKEN\' "$RUNNER_TEMP/operations/worker.py"' not in text

def test_acceptance_run_id_assignments_are_real_separate_shell_assignments():
    text = PRODUCTION_SCRIPT.read_text(encoding="utf-8")
    assert 'RELEASE_RUN_ATTEMPT="${RELEASE_RUN_ATTEMPT:-${GITHUB_RUN_ATTEMPT:-1}}"\nACCEPTANCE_RUN_ID="${GITHUB_RUN_ID}-attempt-${RELEASE_RUN_ATTEMPT}"' in text
    assert 'RELEASE_RUN_ATTEMPT="${RELEASE_RUN_ATTEMPT:-${GITHUB_RUN_ATTEMPT:-1}}"\\nACCEPTANCE_RUN_ID' not in text
    assert 'ACCEPTANCE_RUN_ID="${GITHUB_RUN_ID}-attempt-${RELEASE_RUN_ATTEMPT}"' in text


def test_production_release_acceptance_namespace_uses_authoritative_run_attempt():
    text = PRODUCTION_SCRIPT.read_text(encoding="utf-8")
    workflow = (Path(__file__).parents[1] / ".github" / "workflows" / "heroic-ai-production-release.yml").read_text(encoding="utf-8")
    assert 'RELEASE_RUN_ATTEMPT="${RELEASE_RUN_ATTEMPT:-${GITHUB_RUN_ATTEMPT:-1}}"' in text
    assert 'ACCEPTANCE_RUN_ID="${GITHUB_RUN_ID}-attempt-${RELEASE_RUN_ATTEMPT}"' in text
    assert "RELEASE_RUN_ATTEMPT: ${{ github.run_attempt }}" in workflow


def test_policy_block_acceptance_matches_public_response_contract():
    text = PRODUCTION_SCRIPT.read_text(encoding="utf-8")
    assert '.response.status == "blocked"' in text
    assert '.response.result_state == "BLOCKED"' in text
    assert '.response.operation == "map"' not in text
