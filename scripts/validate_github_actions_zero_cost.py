from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).parents[1]
POLICY_PATH = ROOT / "docs" / "GITHUB_ACTIONS_ZERO_COST_POLICY.json"
WORKFLOW_DIR = ROOT / ".github" / "workflows"

ACTION_REF_RE = re.compile(
    r"^\s*uses:\s*([^\s#]+)(?:\s+#.*)?$"
)
RUNNER_RE = re.compile(r"^\s*runs-on:\s*([^\s#]+)(?:\s+#.*)?$")


def load_policy() -> dict:
    return json.loads(POLICY_PATH.read_text(encoding="utf-8"))


def validate_workflow_text(path: Path, text: str, policy: dict) -> list[str]:
    errors: list[str] = []
    action_policy = policy["action_policy"]
    allowed_refs = set(action_policy["allowed_action_refs"])
    allowed_labels = set(policy["runner_policy"]["allowed_labels"])

    for lineno, line in enumerate(text.splitlines(), start=1):
        runner = RUNNER_RE.match(line)
        if runner:
            label = runner.group(1)
            if label not in allowed_labels:
                errors.append(f"{path}:{lineno}: runner '{label}' is outside the $0 allowlist")

        match = ACTION_REF_RE.match(line)
        if not match:
            continue

        ref = match.group(1)
        if ref.startswith("./"):
            if not action_policy["local_actions_allowed"]:
                errors.append(f"{path}:{lineno}: local Actions are forbidden")
            continue

        if ref.startswith("docker://"):
            if action_policy["docker_actions_allowed"]:
                continue
            errors.append(f"{path}:{lineno}: docker Actions are forbidden by the $0 policy")
            continue

        if "@" not in ref:
            errors.append(f"{path}:{lineno}: Action '{ref}' is not pinned to an immutable SHA")
            continue

        action_name, sha = ref.rsplit("@", 1)
        if not re.fullmatch(r"[0-9a-fA-F]{40}", sha):
            errors.append(f"{path}:{lineno}: Action '{ref}' does not use a full 40-hex commit SHA")
            continue

        if ref not in allowed_refs:
            errors.append(f"{path}:{lineno}: Action '{ref}' is not in the approved $0 allowlist")

    if "zizmorcore/zizmor-action@" in text:
        if not re.search(r"^\s*advanced-security:\s*false\s*$", text, flags=re.MULTILINE):
            errors.append(f"{path}: zizmor must run with advanced-security: false under the $0 policy")

    if "ossf/scorecard-action@" in text:
        if not re.search(r"^\s*publish_results:\s*false\s*$", text, flags=re.MULTILINE):
            errors.append(f"{path}: Scorecard publishing must remain disabled under the $0 policy")

    return errors


def validate_workflows(paths: Iterable[Path] | None = None) -> list[str]:
    policy = load_policy()
    candidates = list(paths) if paths is not None else sorted(
        [*WORKFLOW_DIR.glob("*.yml"), *WORKFLOW_DIR.glob("*.yaml")]
    )
    errors: list[str] = []
    for path in candidates:
        errors.extend(validate_workflow_text(path, path.read_text(encoding="utf-8"), policy))
    return errors


def validate_policy_document() -> None:
    policy = load_policy()
    if policy["schema_version"] != "github-actions-zero-cost-policy/v1":
        raise ValueError("unsupported zero-cost policy schema")
    if policy["repository"] != "Z-Solo-King/foundation":
        raise ValueError("unexpected repository policy target")
    if policy["repository_visibility"] != "public":
        raise ValueError("zero-cost policy requires a public repository")
    invariants = policy["zero_cost_invariants"]
    if invariants["max_additional_cost_usd"] != 0:
        raise ValueError("maximum additional cost must remain $0")
    for key in (
        "external_billing_dependency_allowed",
        "paid_marketplace_action_or_service_allowed",
        "larger_runners_allowed",
        "private_hosted_runner_usage_allowed",
    ):
        if invariants[key] is not False:
            raise ValueError(f"{key} must remain false")
    runners = policy["runner_policy"]
    if runners["full_static_runner_label_required"] is not True:
        raise ValueError("runner labels must remain static")
    if runners["allowed_labels"] != ["ubuntu-latest"]:
        raise ValueError("runner allowlist drift")
    actions = policy["action_policy"]
    if actions["full_sha_required"] is not True:
        raise ValueError("full SHA pinning is mandatory")
    if actions["unknown_action_ref_policy"] != "deny":
        raise ValueError("unknown Action refs must be denied")
    if actions["docker_actions_allowed"] is not False:
        raise ValueError("docker Actions must remain forbidden")
    if len(actions["allowed_action_refs"]) != len(set(actions["allowed_action_refs"])):
        raise ValueError("duplicate Action allowlist entry")
    for ref in actions["allowed_action_refs"]:
        if not re.fullmatch(r".+/[^@]+@[0-9a-fA-F]{40}", ref):
            raise ValueError(f"invalid allowlisted Action ref: {ref}")
    if actions["special_constraints"]["zizmorcore/zizmor-action"]["advanced-security"] is not False:
        raise ValueError("zizmor paid Advanced Security path must remain disabled")
    if actions["special_constraints"]["ossf/scorecard-action"]["publish_results"] is not False:
        raise ValueError("Scorecard publishing must remain disabled")
    provenance = policy["provenance"]
    if provenance["marketplace_is_discovery_only"] is not True:
        raise ValueError("Marketplace must remain discovery-only")


def validate() -> list[str]:
    validate_policy_document()
    return validate_workflows()


if __name__ == "__main__":
    failures = validate()
    if failures:
        print("\n".join(failures))
        raise SystemExit(1)
    print("github actions zero-cost policy: PASS")
