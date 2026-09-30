import test from "node:test";
import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { readFileSync } from "node:fs";

const planner = "tools/multi_lens_planner.mjs";

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
  assert.equal(out.totals.lanes, 3);
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
