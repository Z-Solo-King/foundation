from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).parents[1]
POLICY = ROOT / "docs" / "GITHUB_APP_INTEGRATION_POLICY.json"
CAPABILITY_CATALOG = ROOT / "docs" / "GITHUB_APP_CAPABILITY_CATALOG.json"

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
    catalog = json.loads(CAPABILITY_CATALOG.read_text(encoding="utf-8"))
    if catalog["schema_version"] != "github-app-capability-catalog/v1":
        raise ValueError("unsupported GitHub App capability catalog schema")
    if catalog["source"]["supplied_marketplace_dataset_entries"] != 1408:
        raise ValueError("GitHub App capability catalog source count drift")
    if catalog["principles"]["marketplace_is_discovery_only"] is not True or catalog["principles"]["no_automatic_installation"] is not True:
        raise ValueError("Marketplace discovery-only controls drift")
    contract = policy["integration_contract"]
    ops_app = contract["known_first_party_apps"]["operations_repository_access"]
    if ops_app["marketplace_app"] is not False:
        raise ValueError("Operations App must not be classified as Marketplace")
    if ops_app["repository_scope"] != ["Z-Solo-King/operations"]:
        raise ValueError("Operations App repository scope drift")
    if ops_app["minimum_permissions"] != {"contents": "read"} or ops_app["maximum_permissions"] != {"contents": "read"}:
        raise ValueError("Operations App permission boundary drift")
    if ops_app["token_max_ttl_seconds"] != 3600 or contract["runtime_app_token_rules"]["maximum_token_ttl_seconds"] != 3600:
        raise ValueError("Operations App token lifetime drift")
    if contract["runtime_app_token_rules"]["must_scope_repository_explicitly"] is not True:
        raise ValueError("explicit repository scope rule disabled")
    if policy["schema_version"] != "github-app-integration-policy/v2":
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
    if not all(policy["required_controls"].values()):
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
    for key in ("paid_plans_allowed","free_trials_allowed","payment_method_required","external_billing_dependency_allowed"):
        if zero_cost[key] is not False:
            raise ValueError(f"GitHub App zero-cost control drift: {key}")
    return policy


def validate_first_party_app_workflows() -> None:
    """Validate every Foundation use of the first-party Operations App token action."""
    import re
    workflows = ROOT / ".github" / "workflows"
    token_pattern = re.compile(r"actions/create-github-app-token@([0-9a-f]{40})")
    for path in workflows.rglob("*.yml"):
        lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
        for index, line in enumerate(lines):
            match = token_pattern.search(line)
            if not match:
                continue
            block_lines = []
            for candidate in lines[index:index + 20]:
                if block_lines and candidate.startswith("      - "):
                    break
                block_lines.append(candidate)
            block = "\n".join(block_lines)
            if not re.search(r"client-id:\s*\$\{\{\s*secrets\.OPERATIONS_APP_ID\s*\}\}", block):
                raise ValueError(f"first-party App client-id drift in {path}")
            if not re.search(r"private-key:\s*\$\{\{\s*secrets\.OPERATIONS_APP_PRIVATE_KEY\s*\}\}", block):
                raise ValueError(f"first-party App private-key drift in {path}")
            if not re.search(r"repositories:\s*operations\b", block):
                raise ValueError(f"first-party App repository scope drift in {path}")
            if not re.search(r"permission-contents:\s*read\b", block):
                raise ValueError(f"first-party App contents permission drift in {path}")
            if re.search(r"permission-[A-Za-z0-9_-]+:\s*write\b", block):
                raise ValueError(f"first-party App write permission in {path}")


if __name__ == "__main__":
    validate_policy()
    validate_first_party_app_workflows()
    print("github app integration policy: PASS")
