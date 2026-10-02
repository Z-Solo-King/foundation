import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { loadPolicy, validatePolicyDocument, validateWorkflowText } from "../scripts/validate_github_actions_zero_cost.mjs";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");

test("zero-cost policy document is valid", () => {
  const policy = loadPolicy();
  validatePolicyDocument(policy);
  assert.equal(policy.zero_cost_invariants.max_additional_cost_usd, 0);
  assert.equal(policy.action_policy.full_sha_required, true);
  assert.equal(policy.action_policy.unknown_action_ref_policy, "deny");
});

test("current action allowlist is immutable", () => {
  for (const ref of loadPolicy().action_policy.allowed_action_refs) {
    const [action, sha] = ref.split("@");
    assert.ok(action);
    assert.equal(sha.length, 40);
    assert.match(sha, /^[0-9a-fA-F]{40}$/);
  }
});

test("unknown action and paid runner are rejected", () => {
  const errors = validateWorkflowText("bad.yml", [
    "jobs:",
    "  bad:",
    "    runs-on: ubuntu-latest-xl",
    "    steps:",
    "      - uses: example/vendor-action@0123456789abcdef0123456789abcdef01234567",
  ].join("\n"), loadPolicy());
  assert.ok(errors.some((error) => error.includes("outside the $0 allowlist")));
  assert.ok(errors.some((error) => error.includes("not in the approved $0 allowlist")));
});

test("non-SHA action is rejected", () => {
  const errors = validateWorkflowText("bad.yml", "runs-on: ubuntu-latest\n- uses: example/vendor-action@v1\n", loadPolicy());
  assert.ok(errors.some((error) => error.includes("does not use a full 40-hex commit SHA")));
});

test("docker action is rejected", () => {
  const errors = validateWorkflowText("bad.yml", "runs-on: ubuntu-latest\n- uses: docker://example/image:latest\n", loadPolicy());
  assert.ok(errors.some((error) => error.includes("docker Actions are forbidden")));
});

test("zizmor paid mode is rejected", () => {
  const text = [
    "runs-on: ubuntu-latest",
    "uses: zizmorcore/zizmor-action@cc914d7f3750a2d13d75c7f184a1060aa0e9d482",
    "  advanced-security: true",
  ].join("\n");
  const errors = validateWorkflowText("bad.yml", text, loadPolicy());
  assert.ok(errors.some((error) => error.includes("advanced-security: false")));
});

test("scorecard publishing is rejected", () => {
  const text = [
    "runs-on: ubuntu-latest",
    "uses: ossf/scorecard-action@2d1146689b8cda280b9bc96326124645441f03bc",
    "  publish_results: true",
  ].join("\n");
  const errors = validateWorkflowText("bad.yml", text, loadPolicy());
  assert.ok(errors.some((error) => error.includes("Scorecard publishing")));
});

test("current static-security workflow passes zero-cost rules", () => {
  const workflow = path.join(ROOT, ".github/workflows/actions-static-analysis.yml");
  assert.deepEqual(validateWorkflowText(workflow, fs.readFileSync(workflow, "utf8"), loadPolicy()), []);
});
