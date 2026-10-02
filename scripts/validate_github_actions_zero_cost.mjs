#!/usr/bin/env node
/** Validate Foundation GitHub Actions $0 policy without requiring Python. */
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const POLICY_PATH = path.join(ROOT, "docs", "GITHUB_ACTIONS_ZERO_COST_POLICY.json");
const WORKFLOW_DIR = path.join(ROOT, ".github", "workflows");
const ACTION_REF_RE = /^\s*(?:-\s*)?uses:\s*([^\s#]+)(?:\s+#.*)?$/;
const RUNNER_RE = /^\s*runs-on:\s*([^\s#]+)(?:\s+#.*)?$/;

export function loadPolicy() {
  return JSON.parse(fs.readFileSync(POLICY_PATH, "utf8"));
}

export function validateWorkflowText(filePath, text, policy) {
  const errors = [];
  const actionPolicy = policy.action_policy;
  const allowedRefs = new Set(actionPolicy.allowed_action_refs);
  const allowedLabels = new Set(policy.runner_policy.allowed_labels);

  for (const [index, line] of text.split(/\r?\n/).entries()) {
    const lineNo = index + 1;
    const runner = line.match(RUNNER_RE);
    if (runner && !allowedLabels.has(runner[1])) {
      errors.push(filePath + ":" + lineNo + ": runner '" + runner[1] + "' is outside the $0 allowlist");
    }

    const match = line.match(ACTION_REF_RE);
    if (!match) continue;
    const ref = match[1];

    if (ref.startsWith("./")) {
      if (!actionPolicy.local_actions_allowed) {
        errors.push(filePath + ":" + lineNo + ": local Actions are forbidden");
      }
      continue;
    }

    if (ref.startsWith("docker://")) {
      if (actionPolicy.docker_actions_allowed) continue;
      errors.push(filePath + ":" + lineNo + ": docker Actions are forbidden by the $0 policy");
      continue;
    }

    if (!ref.includes("@")) {
      errors.push(filePath + ":" + lineNo + ": Action '" + ref + "' is not pinned to an immutable SHA");
      continue;
    }

    const sha = ref.slice(ref.lastIndexOf("@") + 1);
    if (!/^[0-9a-fA-F]{40}$/.test(sha)) {
      errors.push(filePath + ":" + lineNo + ": Action '" + ref + "' does not use a full 40-hex commit SHA");
      continue;
    }
    if (!allowedRefs.has(ref)) {
      errors.push(filePath + ":" + lineNo + ": Action '" + ref + "' is not in the approved $0 allowlist");
    }
  }

  if (text.includes("zizmorcore/zizmor-action@") && !/^\s*advanced-security:\s*false\s*$/m.test(text)) {
    errors.push(filePath + ": zizmor must run with advanced-security: false under the $0 policy");
  }
  if (text.includes("ossf/scorecard-action@") && !/^\s*publish_results:\s*false\s*$/m.test(text)) {
    errors.push(filePath + ": Scorecard publishing must remain disabled under the $0 policy");
  }
  return errors;
}

export function validatePolicyDocument(policy = loadPolicy()) {
  if (policy.schema_version !== "github-actions-zero-cost-policy/v1") throw new Error("unsupported zero-cost policy schema");
  if (policy.repository !== "Z-Solo-King/foundation" || policy.repository_visibility !== "public") {
    throw new Error("unexpected zero-cost policy target");
  }

  const invariants = policy.zero_cost_invariants;
  if (invariants.max_additional_cost_usd !== 0) throw new Error("maximum additional cost must remain $0");
  for (const key of [
    "external_billing_dependency_allowed",
    "paid_marketplace_action_or_service_allowed",
    "larger_runners_allowed",
    "private_hosted_runner_usage_allowed",
  ]) {
    if (invariants[key] !== false) throw new Error(key + " must remain false");
  }

  const runners = policy.runner_policy;
  if (runners.full_static_runner_label_required !== true) throw new Error("runner labels must remain static");
  if (JSON.stringify(runners.allowed_labels) !== JSON.stringify(["ubuntu-latest"])) throw new Error("runner allowlist drift");

  const actions = policy.action_policy;
  if (actions.full_sha_required !== true) throw new Error("full SHA pinning is mandatory");
  if (actions.unknown_action_ref_policy !== "deny") throw new Error("unknown Action refs must be denied");
  if (actions.docker_actions_allowed !== false) throw new Error("docker Actions must remain forbidden");
  if (new Set(actions.allowed_action_refs).size !== actions.allowed_action_refs.length) throw new Error("duplicate Action allowlist entry");
  for (const ref of actions.allowed_action_refs) {
    if (!/.+\/[^@]+@[0-9a-fA-F]{40}$/.test(ref)) throw new Error("invalid allowlisted Action ref: " + ref);
  }

  if (actions.special_constraints.zizmorcore["zizmor-action"].advanced-security !== false) {
    throw new Error("zizmor paid Advanced Security path must remain disabled");
  }
  if (actions.special_constraints.ossf["scorecard-action"].publish_results !== false) {
    throw new Error("Scorecard publishing must remain disabled");
  }
  if (policy.provenance.marketplace_is_discovery_only !== true) {
    throw new Error("Marketplace must remain discovery-only");
  }
}

export function validateWorkflows(paths = null) {
  const policy = loadPolicy();
  const files = paths ?? fs.readdirSync(WORKFLOW_DIR)
    .filter((name) => /\.(yml|yaml)$/.test(name))
    .sort()
    .map((name) => path.join(WORKFLOW_DIR, name));
  return files.flatMap((filePath) =>
    validateWorkflowText(filePath, fs.readFileSync(filePath, "utf8"), policy)
  );
}

export function validate() {
  const policy = loadPolicy();
  validatePolicyDocument(policy);
  return validateWorkflows();
}

if (process.argv[1] && fileURLToPath(import.meta.url) === process.argv[1]) {
  const failures = validate();
  if (failures.length) {
    process.stdout.write(failures.join("\n") + "\n");
    process.exitCode = 1;
  } else {
    process.stdout.write("github actions zero-cost policy: PASS\n");
  }
}
