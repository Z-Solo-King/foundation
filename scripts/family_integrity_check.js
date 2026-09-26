#!/usr/bin/env node
"use strict";

const fs = require("fs");
const cp = require("child_process");
const path = require("path");

const ROOT = process.cwd();
const readJson = (p) => JSON.parse(fs.readFileSync(path.join(ROOT, p), "utf8"));
const gh = (repo, api) => {
  const token = repo === "foundation" ? process.env.FOUNDATION_GH_TOKEN : process.env.OPERATIONS_GH_TOKEN;
  if (!token) throw new Error("missing GitHub token for " + repo);
  return JSON.parse(cp.execFileSync("gh", ["api", api, "--paginate"], {
    encoding: "utf8",
    env: { ...process.env, GH_TOKEN: token }
  }));
};

const failures = [];

function fail(msg) {
  failures.push(msg);
  console.error("FAMILY_INTEGRITY_FAIL:", msg);
}

const graph = readJson("docs/FAMILY_INTEGRATION_GRAPH.json");
const matrix = readJson("docs/OPEN_ISSUE_ACCEPTANCE_MATRIX.json");
const taskMatrix = readJson("benchmark/ai_agent_task_matrix_v1.json");
const familyState = readJson("docs/FAMILY_SYNC_STATE.json");
const workflow = fs.readFileSync(path.join(ROOT, ".github/workflows/nightly-ai-research-20jobs.yml"), "utf8");

if (graph.schema !== "family-integration-graph/v1") fail("family graph schema mismatch");
if (graph.status !== "CURRENT") fail("family graph is not CURRENT");
if (Object.keys(graph.material_registry || {}).length !== 20) fail("family graph material registry is not 20");
if ((graph.benchmark_probes || []).length !== 11) fail("family graph probe count is not 11");

const normalizeIssueNumbers = (value) =>
  [...new Set((Array.isArray(value) ? value : [])
    .map(Number)
    .filter((value) => Number.isInteger(value)))]
    .sort((a, b) => a - b);

const normalizeIssueKeys = (pairs) => {
  const normalized = [];
  for (const pair of Array.isArray(pairs) ? pairs : []) {
    const repo = pair && pair[0];
    const number = Number(pair && pair[1]);
    if ((repo === "foundation" || repo === "operations") && Number.isInteger(number) && number > 0) {
      normalized.push(repo + "#" + number);
    }
  }
  return [...new Set(normalized)].sort();
};

const activeIssues = {};
const snapshotPath = process.env.LIVE_ISSUE_SNAPSHOT;
if (snapshotPath) {
  const snapshot = readJson(snapshotPath);
  for (const repo of ["foundation", "operations"]) {
    activeIssues[repo] = normalizeIssueNumbers(
      (snapshot.actual || []).filter(x => x.repo === repo).map(x => x.number)
    );
  }
} else {
  for (const repo of ["foundation", "operations"]) {
    const rows = gh(repo, `repos/Z-Solo-King/${repo}/issues?state=open&per_page=100`);
    activeIssues[repo] = normalizeIssueNumbers(rows.filter(x => !x.pull_request).map(x => x.number));
  }
}

const matrixIssues = normalizeIssueKeys(matrix.issues.map(x => [x.repo, x.number]));

const liveIssuePairs = [
  ...activeIssues.foundation.map(n => ["foundation", n]),
  ...activeIssues.operations.map(n => ["operations", n])
];
const liveIssues = normalizeIssueKeys(liveIssuePairs);

if (JSON.stringify(matrixIssues) !== JSON.stringify(liveIssues)) {
  fail(`acceptance matrix differs from live open issues: matrix=${JSON.stringify(matrixIssues)} live=${JSON.stringify(liveIssues)}`);
}
if (matrix.open_issue_count !== liveIssues.length) fail("acceptance matrix open_issue_count mismatch");

const currentIssueSet = new Set(liveIssues);
for (const probe of graph.benchmark_probes || []) {
  for (const target of probe.targets || []) {
    if (!currentIssueSet.has(target)) fail(`benchmark probe ${probe.id} targets closed/nonexistent issue ${target}`);
  }
}

if (JSON.stringify(normalizeIssueNumbers((taskMatrix.current_issue_targets || {}).foundation)) !== JSON.stringify(activeIssues.foundation)) {
  fail("benchmark current Foundation issue targets differ from live open issues");
}
if (JSON.stringify(normalizeIssueNumbers((taskMatrix.current_issue_targets || {}).operations)) !== JSON.stringify(activeIssues.operations)) {
  fail("benchmark current Operations issue targets differ from live open issues");
}

if (workflow.split("seed_repos:").length - 1 !== 20) fail("nightly research does not contain exactly 20 seed-repository rows");
if (!workflow.includes("max-parallel: 20")) fail("nightly research parallelism is not 20");
if (!workflow.includes('cron: "0 18 * * *"')) fail("nightly research schedule changed");

const staleCorpus = JSON.stringify(taskMatrix);
if (staleCorpus.includes("Foundation #282")) fail("stale Foundation #282 benchmark target exists");
if (staleCorpus.includes("Foundation #154")) fail("closed Foundation #154 benchmark target exists");

if (!familyState.live_main || !familyState.live_main.foundation || !familyState.live_main.operations) {
  fail("family sync state lacks live main heads");
}
if (familyState.current_queue.open_issue_count !== liveIssues.length) {
  fail("family sync state open issue count is stale");
}

if (failures.length) {
  console.error(JSON.stringify({ failures }, null, 2));
  process.exit(1);
}

console.log("FAMILY_INTEGRITY_PASS");
console.log(JSON.stringify({
  live_issues: { foundation: activeIssues.foundation, operations: activeIssues.operations },
  issue_count: liveIssues.length,
  graph_materials: Object.keys(graph.material_registry || {}).length,
  graph_probes: (graph.benchmark_probes || []).length,
  nightly_research_jobs: 20
}, null, 2));
