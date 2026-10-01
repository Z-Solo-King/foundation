from __future__ import annotations

import json
from pathlib import Path

from scripts.validate_github_app_policy import validate_policy


ROOT = Path(__file__).parents[1]
POLICY = ROOT / "docs" / "GITHUB_APP_INTEGRATION_POLICY.json"


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
