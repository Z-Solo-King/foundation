
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
    assert 'wrangler@4.131.1 --config "$d1_migrations_config" d1 execute "$database_name" --remote' in text
    assert text.count('wrangler@4.131.1 --config "$d1_migrations_config" d1 execute "$database_name" --remote') >= 3
    assert "d1 migrations apply" not in text
    assert 'wrangler@4.131.1 d1 migrations apply "$database_name" --remote --config "$d1_migrations_config"' not in text


def test_d1_schema_bootstrap_precedes_python_core_deploy():
    text = PRODUCTION_SCRIPT.read_text(encoding="utf-8")
    schema = '--file="$RUNNER_TEMP/operations/docs/RESOURCE_GOVERNANCE_D1_SCHEMA.sql"'
    core = 'pywrangler deploy --secrets-file "$public_secret_file" --message "github:${GITHUB_SHA}:python-core"'
    assert text.count("RESOURCE_GOVERNANCE_D1_SCHEMA.sql") == 1
    assert text.index(schema) < text.index(core)
    assert "D1 canonical schema bootstrap: PASS" in text

def test_release_d1_commands_use_dedicated_d1_config():
    text = PRODUCTION_SCRIPT.read_text(encoding="utf-8")
    assert 'd1_migrations_config="$RUNNER_TEMP/wrangler.d1.generated.toml"' in text
    assert text.count('d1 execute "$database_name" --remote') >= 3
    assert '--config="$d1_migrations_config"' in text
    assert '--config="$RUNNER_TEMP/operations/wrangler.toml"' not in text

def test_reciprocal_service_bindings_use_binding_free_bootstrap():
    text = (ROOT / "scripts/production_release.sh").read_text(encoding="utf-8")
    assert "Operations binding-free bootstrap deployment: PASS" in text
    assert 'bootstrap_config="$RUNNER_TEMP/operations/wrangler.bootstrap.toml"' in text
    assert '[[services]]' in text
    assert '(cd "$RUNNER_TEMP/operations" && pywrangler deploy --config "$bootstrap_config"' in text