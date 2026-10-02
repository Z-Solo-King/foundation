import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { execFileSync } from "node:child_process";

const ROOT = path.resolve(new URL("..", import.meta.url).pathname);
const TOOL = path.join(ROOT, "tools", "engineering_crossfire.mjs");
const PROFILE = path.join(ROOT, "docs", "ENGINEERING_CROSSFIRE_PROFILE.json");

test("profile fixes the six-lane contract", () => {
  const profile = JSON.parse(fs.readFileSync(PROFILE, "utf8"));
  assert.equal(profile.authority, "diagnostic_only");
  assert.deepEqual(profile.required_lanes, [
    "ownership",
    "contracts",
    "workflows",
    "language",
    "documentation",
    "public-surface"
  ]);
  assert.equal(profile.max_lanes, 6);
  assert.equal(profile.parallel.shared_lane_feedback, false);
  assert.equal(profile.parallel.serialize_mutations, true);
});

test("scanner executes six lanes and emits bounded evidence", () => {
  const output = path.join(ROOT, ".runtime", "test-engineering-crossfire.json");
  execFileSync(process.execPath, [TOOL, "--output", output], { cwd: ROOT, stdio: "pipe" });
  const receipt = JSON.parse(fs.readFileSync(output, "utf8"));
  assert.equal(receipt.schema, "engineering-crossfire-receipt/v1");
  assert.equal(receipt.crossfire.strength, "full_6");
  assert.equal(receipt.crossfire.parallel, true);
  assert.equal(receipt.crossfire.shared_lane_feedback, false);
  assert.equal(receipt.crossfire.mutation_phase, "separate");
  assert.equal(receipt.lanes.length, 6);
  for (const lane of receipt.lanes) {
    assert.equal(lane.status, "completed");
    assert.match(lane.finding_digest, /^[a-f0-9]{64}$/);
  }
});
