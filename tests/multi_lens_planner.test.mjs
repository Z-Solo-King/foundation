import test from "node:test";
import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const here = dirname(fileURLToPath(import.meta.url));
const planner = join(here, "..", "tools", "multi_lens_planner.mjs");

function run(input) {
  const p = spawnSync(process.execPath, [planner], {
    input: JSON.stringify(input),
    encoding: "utf8",
  });
  assert.equal(p.status, 0, p.stderr);
  return JSON.parse(p.stdout);
}

test("selects required lanes before adaptive lanes", () => {
  const out = run({
    target: "demo",
    max_lanes: 3,
    cost_budget: 10,
    latency_budget: 100,
    quota_budget: 100,
    lanes: [
      { id: "cheap", family: "search", coverage_gain: 0.7, failure_detection: 0.2, confidence_gain: 0.4, execution_cost: 1, latency_cost: 1, quota_cost: 0 },
      { id: "required", family: "security", required: true, coverage_gain: 0.2, failure_detection: 1, confidence_gain: 0.8, execution_cost: 2, latency_cost: 3, quota_cost: 0 },
      { id: "expensive", family: "browser", coverage_gain: 1, failure_detection: 0.7, confidence_gain: 0.9, execution_cost: 20, latency_cost: 50, quota_cost: 10 }
    ]
  });
  assert.equal(out.selected[0].id, "required");
  assert.equal(out.selected[0].selection, "required");
  assert.equal(out.totals.lanes, 2);
});

test("keeps untested lanes alive through exploration", () => {
  const out = run({
    target: "demo",
    max_lanes: 2,
    cost_budget: 10,
    latency_budget: 100,
    quota_budget: 100,
    total_verified_lanes: 100,
    lanes: [
      { id: "known", family: "search", coverage_gain: 0.9, failure_detection: 0.2, confidence_gain: 0.5, execution_cost: 1, latency_cost: 1, quota_cost: 0 },
      { id: "new", family: "browser", coverage_gain: 0.6, failure_detection: 0.6, confidence_gain: 0.6, execution_cost: 1, latency_cost: 1, quota_cost: 0 }
    ],
    history: {
      known: { runs: 100, novel_finding_rate: 0.05, evidence_acceptance_rate: 0.9 }
    }
  });
  assert.ok(out.selected.some((x) => x.id === "new"));
});

test("never silently drops a required lane when over budget", () => {
  const out = run({
    target: "demo",
    max_lanes: 1,
    cost_budget: 1,
    latency_budget: 10,
    quota_budget: 10,
    lanes: [
      { id: "required", family: "security", required: true, coverage_gain: 1, failure_detection: 1, confidence_gain: 1, execution_cost: 2, latency_cost: 1, quota_cost: 0 }
    ]
  });
  assert.equal(out.selected.length, 0);
  assert.equal(out.skipped[0].skip_reason, "budget_or_lane_limit");
  assert.equal(out.skipped[0].selection, "required-but-blocked");
});

test("output is deterministic", () => {
  const input = {
    target: "demo",
    max_lanes: 3,
    lanes: [
      { id: "b", family: "runtime", coverage_gain: 0.5, failure_detection: 0.5, confidence_gain: 0.5, execution_cost: 1, latency_cost: 1, quota_cost: 0 },
      { id: "a", family: "search", coverage_gain: 0.5, failure_detection: 0.5, confidence_gain: 0.5, execution_cost: 1, latency_cost: 1, quota_cost: 0 }
    ]
  };
  assert.deepEqual(run(input), run(input));
});

assert.ok(readFileSync(planner, "utf8").includes("scheduling_only"));

test("honors profile defaults and required IDs", () => {
  const out = run({
    target_defaults: { max_lanes: 2, cost_budget: 4, latency_budget: 20, quota_budget: 20, freshness_need: 0.4 },
    required_ids: ["provider"],
    lanes: [
      { id: "provider", family: "ai_provider", coverage_gain: 0.4, failure_detection: 0.8, confidence_gain: 0.8, execution_cost: 1, latency_cost: 2, quota_cost: 1 },
      { id: "other", family: "search", coverage_gain: 0.7, failure_detection: 0.5, confidence_gain: 0.6, execution_cost: 1, latency_cost: 2, quota_cost: 0 }
    ]
  });
  assert.equal(out.constraints.max_lanes, 2);
  assert.equal(out.selected[0].id, "provider");
  assert.equal(out.selected[0].selection, "required");
});

test("orders dependent lanes into later batches", () => {
  const out = run({
    max_lanes: 3,
    cost_budget: 5,
    latency_budget: 50,
    quota_budget: 20,
    lanes: [
      { id: "dependent", family: "browser", depends_on: ["base"], coverage_gain: 0.9, failure_detection: 0.9, confidence_gain: 0.9, execution_cost: 1, latency_cost: 5, quota_cost: 0 },
      { id: "base", family: "search", coverage_gain: 0.5, failure_detection: 0.5, confidence_gain: 0.5, execution_cost: 1, latency_cost: 2, quota_cost: 0 }
    ]
  });
  assert.deepEqual(out.selected.map((x) => [x.id, x.batch]), [["base", 0], ["dependent", 1]]);
});

test("enforces an explicit exclusive group", () => {
  const out = run({
    max_lanes: 3,
    cost_budget: 5,
    latency_budget: 50,
    quota_budget: 20,
    lanes: [
      { id: "engine-a", family: "browser", exclusive_group: "browser-choice", coverage_gain: 0.8, failure_detection: 0.8, confidence_gain: 0.8, execution_cost: 1, latency_cost: 2, quota_cost: 0 },
      { id: "engine-b", family: "browser", exclusive_group: "browser-choice", coverage_gain: 0.7, failure_detection: 0.7, confidence_gain: 0.7, execution_cost: 1, latency_cost: 2, quota_cost: 0 }
    ]
  });
  assert.equal(out.selected.length, 1);
  assert.equal(out.skipped[0].skip_reason, "exclusive_group_conflict");
});
