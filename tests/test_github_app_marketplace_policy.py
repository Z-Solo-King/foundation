from __future__ import annotations

import json
from pathlib import Path

from scripts.validate_github_app_policy import validate_first_party_app_workflows, validate_policy


ROOT = Path(__file__).parents[1]
POLICY = ROOT / "docs" / "GITHUB_APP_INTEGRATION_POLICY.json"


def test_github_app_capability_catalog_is_present() -> None:
    catalog = json.loads((ROOT / "docs" / "GITHUB_APP_CAPABILITY_CATALOG.json").read_text(encoding="utf-8"))
    assert catalog["schema_version"] == "github-app-capability-catalog/v1"
    assert catalog["source"]["supplied_marketplace_dataset_entries"] == 1408
    assert catalog["principles"]["marketplace_is_discovery_only"] is True
    assert catalog["principles"]["no_automatic_installation"] is True


def test_first_party_operations_app_contract_is_bounded() -> None:
    policy = validate_policy()
    app = policy["integration_contract"]["known_first_party_apps"]["operations_repository_access"]
    assert app["marketplace_app"] is False
    assert app["repository_scope"] == ["Z-Solo-King/operations"]
    assert app["minimum_permissions"] == {"contents": "read"}
    assert app["maximum_permissions"] == {"contents": "read", "issues": "write"}
    assert app["scoped_write_exceptions"][0]["workflow"] == ".github/workflows/twice-daily-governance-sweep.yml"
    assert app["scoped_write_exceptions"][0]["permissions"] == {"issues": "write"}
    assert app["token_max_ttl_seconds"] == 3600


def test_all_create_app_token_workflows_use_the_bounded_operations_app() -> None:
    validate_first_party_app_workflows()


def test_github_app_policy_is_valid() -> None:
    policy = validate_policy()
    assert policy["marketplace_installation_default"] == "disabled"
    assert policy["installation_requires_explicit_approval"] is True
    assert policy["external_marketplace_apps"] == []
    assert policy["zero_cost_policy"]["max_additional_cost_usd"] == 0
    assert policy["zero_cost_policy"]["paid_plans_allowed"] is False
    assert policy["zero_cost_policy"]["free_trials_allowed"] is False
    assert policy["zero_cost_policy"]["payment_method_required"] is False
    assert policy["zero_cost_policy"]["external_billing_dependency_allowed"] is False


def test_github_app_policy_forbids_production_authority() -> None:
    policy = json.loads(POLICY.read_text(encoding="utf-8"))
    assert policy["app_roles"]["deployment"] == "forbidden"
    assert policy["app_roles"]["production_authority"] == "forbidden"
    assert policy["required_controls"]["no_secret_mutation_authority"] is True
    assert policy["required_controls"]["no_production_deploy_authority"] is True


def test_github_app_policy_limits_repository_scope() -> None:
    policy = json.loads(POLICY.read_text(encoding="utf-8"))
    assert set(policy["allowed_repository_scope"]) == {
        "Z-Solo-King/foundation",
        "Z-Solo-King/operations",
    }
    assert policy["permission_baseline"] == {
        "contents": "read",
        "issues": "read",
        "pull_requests": "read",
        "actions": "read",
    }


def test_operations_app_write_scope_is_exactly_governance_issue_only() -> None:
    policy = validate_policy()
    app = policy["integration_contract"]["known_first_party_apps"]["operations_repository_access"]
    exceptions = app["scoped_write_exceptions"]
    assert len(exceptions) == 1
    assert exceptions[0]["repository_scope"] == ["Z-Solo-King/operations"]
    assert exceptions[0]["permissions"] == {"issues": "write"}
