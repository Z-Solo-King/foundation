import test from "node:test";
import assert from "node:assert/strict";
import { collectFindings, buildIssueBody, TRACKING_LABEL, TRACKING_TITLE } from "../scripts/publish_benchmark_findings.mjs";

test("instruction finding becomes issue candidate", () => {
  const report = {
    schema: "instruction-audit/v1",
    finding_count: 1,
    findings: [{ kind: "duplicate", document: "AGENTS.md", line: 4, detail: "matches CLAUDE.md:7" }],
  };
  const findings = collectFindings(report, null);
  assert.equal(findings.length, 1);
  const body = buildIssueBody(findings, "123", "Z-Solo-King/foundation");
  assert.match(body, /# Automated benchmark findings/);
  assert.equal(TRACKING_TITLE, "Nightly benchmark findings — automated tracking");
  assert.equal(TRACKING_LABEL, "benchmark-finding");
  assert.match(body, /does not authorize policy/);
});

test("benchmark hard-gate failure is consumed", () => {
  const findings = collectFindings(null, { hard_gate_failures: ["security"] });
  assert.equal(findings[0].kind, "hard-gate-failure");
});

test("normal benchmark report has no finding", () => {
  const report = { hard_gate_rule: "numeric observations never override security/policy/provenance/runtime/production gates" };
  assert.deepEqual(collectFindings(null, report), []);
});
