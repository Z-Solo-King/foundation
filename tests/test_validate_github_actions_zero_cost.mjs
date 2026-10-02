import test from "node:test";
import assert from "node:assert/strict";
import { loadPolicy, validateWorkflowText, validatePolicyDocument } from "../scripts/validate_github_actions_zero_cost.mjs";

test("zero-cost policy document remains internally valid", () => {
  validatePolicyDocument(loadPolicy());
});

test("pinned allowlisted workflow passes", () => {
  const policy = loadPolicy();
  const text = [
    "runs-on: ubuntu-latest",
    "uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1",
  ].join("\n");
  assert.deepEqual(validateWorkflowText("sample.yml", text, policy), []);
});

test("unpinned action is rejected", () => {
  const policy = loadPolicy();
  const errors = validateWorkflowText("sample.yml", "uses: actions/checkout@v7", policy);
  assert.equal(errors.length, 1);
  assert.match(errors[0], /does not use a full 40-hex commit SHA/);
});
