import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { buildScan } from "../tools/comprehensive_governance_scan.mjs";

const ROOT = path.resolve(".");

function write(root, rel, text) {
  const file = path.join(root, rel);
  fs.mkdirSync(path.dirname(file), { recursive: true });
  fs.writeFileSync(file, text);
}

test("governance contract keeps eight lanes", () => {
  const payload = JSON.parse(fs.readFileSync(path.join(ROOT, "docs/AUTONOMOUS_GOVERNANCE_SCAN_CONTRACT.json"), "utf8"));
  assert.equal(payload.schema, "autonomous-governance-scan/v1");
  assert.equal(payload.lanes.length, 8);
  assert.match(payload.cross_product.n2xn2, /^Use bounded/);
});

test("Node scanner contains canonical control surfaces", () => {
  const source = fs.readFileSync(path.join(ROOT, "tools/comprehensive_governance_scan.mjs"), "utf8");
  for (const needle of [
    "exact_duplicate_content",
    "cross_repo_duplicate_content",
    "private_tree_in_public_repo",
    "migration_gate_incomplete",
    "critical_source_size",
    "task_family_parity",
    "quality_hard_gate_incomplete",
    "bounded_feature_policy_cross_product",
    "unregistered_privileged_workflow",
    "slow_workflow_runs",
    "migration_candidate_missing_evidence",
    "canonical_policy_surface_missing",
    "canonical_runtime_surface_missing",
    "attention_source_size",
  ]) assert.ok(source.includes(needle), needle);
});

test("scanner captures language distribution without becoming authority", () => {
  const foundation = fs.mkdtempSync(path.join(os.tmpdir(), "gov-foundation-"));
  const operations = fs.mkdtempSync(path.join(os.tmpdir(), "gov-operations-"));
  try {
    for (const [rel,text] of [
      ["README.md", "# fixture\n"],
      [".github/workflows/example.yml", "permissions:\n  contents: read\n"],
      ["tool.py", "print('x')\n"],
      ["edge.ts", "export const edge = true;\n"],
    ]) write(foundation, rel, text);
    for (const [rel,text] of [
      ["docs/AI_PROVIDER_TASK_FABRIC_2026-09-30.json", "{\"external_providers\":[] ,\"task_families\":[]}\n"],
      ["polyglot/REGISTRY.json", "{\"registry_policy\":{\"active_diversity\":{\"current_runtime_set\":[\"python\"]}},\"candidates\":[]}\n"],
      ["docs/MIGRATION_EVIDENCE_MATRIX.json", "{\"required_gates\":[],\"candidates\":[]}\n"],
      ["private/runtime_language_policy.py", "x\n"],
      ["private/search_provider_catalog.py", "x\n"],
      ["private/search_provider_capabilities.py", "x\n"],
      ["private/search_rate_limit.py", "x\n"],
      ["private/search_route_policy.py", "x\n"],
      ["private/search_provider_execution.py", "x\n"],
      ["private/chatbot/chat_endpoint.py", "x\n"],
      ["private/audit_rule_catalog.py", "x\n"],
      ["private/language_governance_policy.py", "x\n"],
      ["private/evolution_score.py", "x\n"],
      ["private/evolution_engine.py", "x\n"],
      ["private/evolution_integration.py", "x\n"],
      ["private/self_evolution_boundary.py", "x\n"],
      ["private/strategy_matrix.py", "x\n"],
      ["private/ai_maintainability_policy.py", "x\n"],
      ["private/language_fit_policy.py", "x\n"],
      ["private/migration_artifact_policy.py", "x\n"],
      ["private/chatbot/chat_learning.py", "x\n"],
      ["private/chatbot/chat_learning_index.py", "x\n"],
      ["private/chatbot/feedback_evaluation_bridge.py", "x\n"],
      ["docs/PROJECT_OBSERVABILITY_AND_EVOLUTION.md", "x\n"],
      ["docs/FEATURE_SURFACE_GOVERNANCE_POLICY.json", "{}\n"],
    ]) write(operations, rel, text);

    const result = buildScan(foundation, operations, {}, "migration_boundary");
    assert.equal(result.schema, "comprehensive-governance-scan/v1");
    const language = result.findings.find(x => x.code === "language_distribution");
    assert.ok(language);
    assert.equal(language.severity, "info");
    assert.equal(result.authority_note.includes("remain canonical"), true);
  } finally {
    fs.rmSync(foundation, { recursive: true, force: true });
    fs.rmSync(operations, { recursive: true, force: true });
  }
});

test("Node scanner output is deterministic for a fixed inventory snapshot", () => {
  const foundation = fs.mkdtempSync(path.join(os.tmpdir(), "gov-foundation-det-"));
  const operations = fs.mkdtempSync(path.join(os.tmpdir(), "gov-operations-det-"));
  try {
    write(foundation, "tool.py", "print('x')\n");
    write(operations, "private/runtime_language_policy.py", "x\n");
    const a = buildScan(foundation, operations, {}, "structure_hygiene");
    const b = buildScan(foundation, operations, {}, "structure_hygiene");
    delete a.findings;
    delete b.findings;
    assert.deepEqual(a, b);
  } finally {
    fs.rmSync(foundation, { recursive: true, force: true });
    fs.rmSync(operations, { recursive: true, force: true });
  }
});
