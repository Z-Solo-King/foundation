#!/usr/bin/env node
"use strict";

/**
 * Deterministic CrossFire coverage scanner.
 *
 * This is a coverage/quality gate, not a policy or acceptance authority.
 * It checks whether important project surfaces retain multiple independent
 * verification paths and whether the canonical multi-lens contracts remain
 * present. It never dispatches workflows or mutates repository state.
 */

import fs from "node:fs";
import path from "node:path";

export const CROSSFIRE_SURFACES = Object.freeze({
  audit: ["exhaustive-six-lane-audit.yml", "cross-repository-contract-drift.yml"],
  runtime: ["provider-fleet-runtime-state.yml", "nightly-invariants.yml"],
  provider: ["live-ai-provider-crossfire.yml", "provider-fleet-runtime-state.yml"],
  extraction: ["live-extractor-benchmark.yml", "extractor-surface-governance.yml"],
  chatbot: ["live-chatbot-production-smoke.yml", "live-ai-agent-benchmark.yml"],
  research: ["nightly-multi-agent-research-v3.yml", "live-nightly-research-canary.yml"],
  security: ["full-history-secret-scan.yml", "codeql.yml", "actions-static-analysis.yml"],
  migration: ["polyglot-migration-review.yml", "open-issue-polyglot-deep-scan.yml"],
});

export const CROSSFIRE_CONTRACTS = Object.freeze({
  "docs/CROSS_SYSTEM_CROSSFIRE_STANDARD.md": ["fan-out", "contradiction", "receipt-backed"],
  "docs/MULTI_LENS_EXECUTION_ENGINE.md": ["adaptive lane", "negative-space-audit", "mutation-audit"],
  "docs/AI_AUDIT_SYSTEM.md": ["independent checks", "CrossFire"],
});

function readText(root, relativePath) {
  const filename = path.join(root, relativePath);
  return fs.existsSync(filename) ? fs.readFileSync(filename, "utf8") : "";
}

function workflowFiles(root) {
  const dir = path.join(root, ".github", "workflows");
  if (!fs.existsSync(dir)) return [];
  return fs.readdirSync(dir).filter((name) => name.endsWith(".yml") || name.endsWith(".yaml")).sort();
}

export function inspectCrossfireCoverage(root = process.cwd()) {
  const files = workflowFiles(root);
  const available = new Set(files);
  const surfaces = Object.fromEntries(
    Object.entries(CROSSFIRE_SURFACES).map(([surface, required]) => {
      const found = required.filter((name) => available.has(name));
      return [surface, {
        required: [...required],
        found,
        missing: required.filter((name) => !available.has(name)),
        independent_paths: found.length,
        minimum_paths: 2,
        passed: found.length >= 2,
      }];
    }),
  );

  const contracts = Object.fromEntries(
    Object.entries(CROSSFIRE_CONTRACTS).map(([file, markers]) => {
      const text = readText(root, file);
      const missing = markers.filter((marker) => !text.toLowerCase().includes(marker.toLowerCase()));
      return [file, {
        required_markers: [...markers],
        missing,
        passed: fs.existsSync(path.join(root, file)) && missing.length === 0,
      }];
    }),
  );

  const workflowText = files.map((name) => readText(root, path.join(".github", "workflows", name))).join("\n");
  const uses = [...workflowText.matchAll(/^\s*uses:\s*([^\s#]+)/gm)].map((match) => match[1]);
  const pinned = uses.filter((ref) => /@([0-9a-f]{40})$/i.test(ref));
  const unpinned = uses.filter((ref) => !/@([0-9a-f]{40})$/i.test(ref));

  const failures = [
    ...Object.entries(surfaces)
      .filter(([, result]) => !result.passed)
      .map(([surface, result]) => ({
        code: "surface_insufficient_independent_paths",
        surface,
        missing: result.missing,
      })),
    ...Object.entries(contracts)
      .filter(([, result]) => !result.passed)
      .map(([file, result]) => ({
        code: "crossfire_contract_missing_marker",
        file,
        missing: result.missing,
      })),
  ];

  return {
    schema: "crossfire-coverage/v1",
    workflow_count: files.length,
    surfaces,
    contracts,
    action_reference_audit: {
      total_uses: uses.length,
      pinned_refs: pinned.length,
      unpinned_refs: unpinned,
    },
    failures,
    passed: failures.length === 0,
    authority: "coverage_and_scheduling_only",
  };
}

if (process.argv[1] && path.resolve(process.argv[1]) === path.resolve(new URL(import.meta.url).pathname)) {
  const root = process.argv[2] ? path.resolve(process.argv[2]) : process.cwd();
  const result = inspectCrossfireCoverage(root);
  console.log(JSON.stringify(result, null, 2));
  process.exitCode = result.passed ? 0 : 1;
}
