from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).parents[1]
POLICY = ROOT / "docs" / "GITHUB_APP_INTEGRATION_POLICY.json"

ALLOWED_SCOPES = {
    "Z-Solo-King/foundation",
    "Z-Solo-King/operations",
}
BASELINE_KEYS = {"contents", "issues", "pull_requests", "actions"}
ALLOWED_ROLES = {
    "security",
    "code_review",
    "ai_agent",
    "project_management",
    "observability",
    "deployment",
    "production_authority",
}


def validate_policy() -> dict:
    policy = json.loads(POLICY.read_text(encoding="utf-8"))
    if policy["schema_version"] != "github-app-integration-policy/v1":
        raise ValueError("unsupported GitHub App policy schema")
    if policy["marketplace_installation_default"] != "disabled":
        raise ValueError("Marketplace app installation must default to disabled")
    if policy["installation_requires_explicit_approval"] is not True:
        raise ValueError("Marketplace installations require explicit approval")
    if set(policy["allowed_repository_scope"]) != ALLOWED_SCOPES:
        raise ValueError("unexpected repository scope")
    if policy["external_marketplace_apps"] != []:
        raise ValueError("no external Marketplace App may be activated through this policy")
    if set(policy["permission_baseline"]) != BASELINE_KEYS:
        raise ValueError("permission baseline drift")
    required_controls = policy["required_controls"]
    if not all(required_controls.values()):
        raise ValueError("a required GitHub App security control is disabled")
    roles = policy["app_roles"]
    if set(roles) != ALLOWED_ROLES:
        raise ValueError("unexpected app role")
    if roles["deployment"] != "forbidden":
        raise ValueError("deployment role must remain forbidden")
    if roles["production_authority"] != "forbidden":
        raise ValueError("production authority must remain forbidden")
    if policy["webhook_policy"]["enabled_by_default"] is not False:
        raise ValueError("webhooks must be opt-in")
    if policy["webhook_policy"]["signature_validation_required"] is not True:
        raise ValueError("webhook signature validation is mandatory")
    if policy["provenance"]["marketplace_is_discovery_only"] is not True:
        raise ValueError("Marketplace must remain a discovery source")

    zero_cost = policy["zero_cost_policy"]
    if zero_cost["max_additional_cost_usd"] != 0:
        raise ValueError("GitHub Apps maximum additional cost must remain $0")
    for key in (
        "paid_plans_allowed",
        "free_trials_allowed",
        "payment_method_required",
        "external_billing_dependency_allowed",
    ):
        if zero_cost[key] is not False:
            raise ValueError(f"GitHub App zero-cost control drift: {key}")

    return policy


if __name__ == "__main__":
    validate_policy()
    print("github app integration policy: PASS")
