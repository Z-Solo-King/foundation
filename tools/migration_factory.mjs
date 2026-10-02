#!/usr/bin/env node
import { execFileSync } from "node:child_process";
import { createHash } from "node:crypto";
import { readFileSync, writeFileSync, statSync } from "node:fs";
import { join } from "node:path";

const args = new Map();
for (let i = 2; i < process.argv.length; i++) {
  const key = process.argv[i];
  if (key.startsWith("--")) args.set(key, process.argv[++i] ?? "");
}

const root = args.get("--root") || ".";
const lane = args.get("--lane") || "inventory";
const out = args.get("--out") || ".runtime/migration-factory-" + lane + ".json";
const lanes = new Set([
  "runtime-frontier",
  "dependency-frontier",
  "tooling-ci",
  "tests-benchmarks",
  "target-language",
  "retirement-readiness",
]);
if (!lanes.has(lane)) throw new Error("unknown migration factory lane: " + lane);

const run = (cmd, argv) => execFileSync(cmd, argv, {
  cwd: root,
  encoding: "utf8",
  maxBuffer: 8 * 1024 * 1024,
}).trim();

const tracked = run("git", ["ls-files", "-z"]).split("\0").filter(Boolean);
const pythonFiles = tracked.filter((p) => p.endsWith(".py")).sort();

function read(p) {
  try {
    const st = statSync(join(root, p));
    if (!st.isFile() || st.size > 2_000_000) return "";
    return readFileSync(join(root, p), "utf8");
  } catch {
    return "";
  }
}
const norm = (p) => p.replaceAll("\\", "/");

function classify(p) {
  const x = norm(p);
  if (/(^|\/)tests?\//.test(x) || /(^|\/)test_[^/]+\.py$/.test(x)) return "test";
  if (x.includes("/benchmark/") || x.startsWith("benchmark/")) return "benchmark";
  if (x.includes("/tools/") || x.startsWith("tools/") || x.includes("/scripts/") || x.startsWith("scripts/")) return "tooling";
  if (x.includes("/archive/") || x.includes("/history/") || x.includes("/retired/")) return "archive";
  if (x.startsWith("foundation_core/") || x.startsWith("backend/") || x.startsWith("private/") ||
      /(^|\/)(worker|foundation_worker)\.py$/.test(x) || x.startsWith("extractor_mapper/")) return "runtime";
  return "other";
}

function targetFor(p) {
  const x = norm(p);
  if (/private\/(policy|resource_ledger|durable_resource_ledger|promotion|artifact_manifest|audit_provenance|replay|idempotency)/.test(x) ||
      /backend\/persistence/.test(x)) {
    return { language: "retain-python", disposition: "RETAIN", confidence: 0.98, reason: "protected authority; requires separate authority migration" };
  }
  if (/url|canonical/i.test(x) || /text_normalization|html_kernel|jsonld|robots|sitemap|link_pagination|product_mapping/.test(x)) {
    return { language: "rust", disposition: "MIGRATE", confidence: 0.90, reason: "deterministic parsing/normalization/CPU-bound kernel" };
  }
  if (/edge|sse|search|browser|endpoint|acquisition|next_data|stream/i.test(x)) {
    return { language: "typescript", disposition: "MIGRATE", confidence: 0.90, reason: "edge/browser/search/provider boundary" };
  }
  if (/fanout/i.test(x)) {
    return { language: "go", disposition: "MIGRATE", confidence: 0.90, reason: "bounded high-concurrency network tooling" };
  }
  const kind = classify(p);
  if (kind === "tooling") return { language: "node-or-shell", disposition: "MIGRATE", confidence: 0.85, reason: "repository automation should not require Python where avoidable" };
  if (kind === "test" || kind === "benchmark") return { language: "follow-production-owner", disposition: "FOLLOW", confidence: 0.99, reason: "verification follows the migrated production responsibility" };
  if (kind === "archive") return { language: "none", disposition: "ARCHIVE", confidence: 1, reason: "historical material is provenance, not runtime" };
  return { language: "review-required", disposition: "REVIEW REQUIRED", confidence: 0, reason: "no safe automatic target from path semantics" };
}

const pythonBodies = new Map();
for (const p of pythonFiles) pythonBodies.set(p, read(p));

const nonPythonTextFiles = tracked.filter((p) =>
  !p.endsWith(".py") &&
  !p.endsWith(".lock") &&
  !p.startsWith(".git/")
).sort();

const nonPythonRefs = new Map(pythonFiles.map((p) => [p, []]));
const ciPythonRefs = [];
const pythonPathModules = new Map(
  pythonFiles.map((p) => [p.slice(0, -3).replaceAll("/", "."), p])
);

for (const p of nonPythonTextFiles) {
  const body = read(p);
  if (!body) continue;
  const x = norm(p);
  if (x.startsWith(".github/workflows/") && /\bpython(?:3)?\b|\.py\b|pytest|pip\b/.test(body)) {
    ciPythonRefs.push(x);
  }
  for (const [module, py] of pythonPathModules) {
    if (body.includes(py) || body.includes(module)) nonPythonRefs.get(py).push(x);
  }
}

function runtimeSignals(path, body) {
  return {
    worker_entrypoint: /WorkerEntrypoint|export\s+default|async\s+def\s+scheduled\b|async\s+def\s+fetch\b/.test(body),
    main_entrypoint: /if\s+__name__\s*==\s*["']__main__["']/.test(body),
    exported_symbols: (body.match(/^(?:async\s+)?(?:def|class)\s+\w+/gm) || []).length,
  };
}

const rows = pythonFiles.map((path) => {
  const body = pythonBodies.get(path) || "";
  const imports = [];
  const impRE = /(?:^|\n)\s*(?:from|import)\s+([A-Za-z_][\w.]*)/g;
  for (const m of body.matchAll(impRE)) imports.push(m[1]);

  const classification = classify(path);
  const target = targetFor(path);
  const refs = [...new Set(nonPythonRefs.get(path) || [])].sort();

  return {
    path,
    class: classification,
    target_language: target.language,
    disposition: target.disposition,
    target_confidence: target.confidence,
    target_reason: target.reason,
    imports: [...new Set(imports)].slice(0, 120),
    imported_local_python_modules: [...new Set(imports.map((m) => pythonPathModules.get(m)).filter(Boolean))],
    non_python_references: refs.slice(0, 100),
    non_python_reference_count: refs.length,
    has_subprocess: /subprocess|os\.system|Popen/.test(body),
    has_exec_python: /python(?:3)?\s+-m|sys\.executable/.test(body),
    has_network: /requests|httpx|urllib|aiohttp/.test(body),
    has_state: /sqlite|d1|redis|kv|durable|ledger|persistence/.test(body),
    runtime_signals: runtimeSignals(path, body),
    lane,
  };
});

const inventoryDigest = createHash("sha256")
  .update(pythonFiles.map(norm).join("\n"), "utf8")
  .digest("hex");

const countBy = (key) => rows.reduce((acc, row) => {
  acc[row[key]] = (acc[row[key]] || 0) + 1;
  return acc;
}, {});

const laneFindings = {
  "runtime-frontier": {
    runtime_files: rows.filter((r) => r.class === "runtime").length,
    entrypoints: rows.filter((r) => r.runtime_signals.worker_entrypoint || r.runtime_signals.main_entrypoint).map((r) => r.path),
    stateful_runtime_files: rows.filter((r) => r.class === "runtime" && r.has_state).map((r) => r.path),
  },
  "dependency-frontier": {
    files_with_local_python_imports: rows.filter((r) => r.imported_local_python_modules.length > 0).map((r) => ({ path:r.path, modules:r.imported_local_python_modules })),
    subprocess_python_edges: rows.filter((r) => r.has_exec_python || r.has_subprocess).map((r) => r.path),
  },
  "tooling-ci": {
    python_ci_reference_paths: [...new Set(ciPythonRefs)].sort(),
    python_tooling_files: rows.filter((r) => r.class === "tooling").map((r) => r.path),
  },
  "tests-benchmarks": {
    tests: rows.filter((r) => r.class === "test").map((r) => r.path),
    benchmarks: rows.filter((r) => r.class === "benchmark").map((r) => r.path),
    follow_count: rows.filter((r) => r.disposition === "FOLLOW").length,
  },
  "target-language": {
    migration_targets: rows.filter((r) => r.disposition === "MIGRATE").map((r) => ({ path:r.path, language:r.target_language, confidence:r.target_confidence })),
    retained: rows.filter((r) => r.disposition === "RETAIN").map((r) => r.path),
    review_required: rows.filter((r) => r.disposition === "REVIEW REQUIRED").map((r) => r.path),
  },
  "retirement-readiness": {
    python_files_referenced_by_non_python: rows.filter((r) => r.non_python_reference_count > 0).map((r) => ({ path:r.path, reference_count:r.non_python_reference_count, refs:r.non_python_references })),
    executable_python_edges: rows.filter((r) => r.has_exec_python).map((r) => r.path),
    deletion_candidates: rows.filter((r) => ["ARCHIVE","DELETE"].includes(r.disposition) && r.non_python_reference_count === 0).map((r) => r.path),
  },
};

const report = {
  schema: "polyglot-migration-factory/v2",
  generated_at: new Date().toISOString(),
  repository: run("git", ["remote", "get-url", "origin"]),
  revision: run("git", ["rev-parse", "HEAD"]),
  lane,
  coverage: {
    expected_python_files: pythonFiles.length,
    reported_python_files: rows.length,
    unique_python_files: new Set(rows.map((r) => r.path)).size,
    inventory_digest: inventoryDigest,
    complete: rows.length === pythonFiles.length && new Set(rows.map((r) => r.path)).size === pythonFiles.length,
  },
  counts: {
    class: countBy("class"),
    disposition: countBy("disposition"),
    target_language: countBy("target_language"),
  },
  lane_findings: laneFindings[lane],
  blockers: {
    python_runtime_files: rows.filter((r) => r.class === "runtime").length,
    python_tooling_files: rows.filter((r) => r.class === "tooling").length,
    python_tests_and_benchmarks: rows.filter((r) => ["test","benchmark"].includes(r.class)).length,
    retained_python_authority: rows.filter((r) => r.disposition === "RETAIN").length,
    review_required: rows.filter((r) => r.disposition === "REVIEW REQUIRED").length,
    non_python_reference_edges: rows.reduce((n,r)=>n+r.non_python_reference_count,0),
    python_subprocess_edges: rows.filter((r) => r.has_exec_python).length,
  },
  files: rows,
};

if (!report.coverage.complete) throw new Error("python inventory coverage is incomplete");
writeFileSync(join(root, out), JSON.stringify(report, null, 2) + "\n");
console.log(JSON.stringify({
  schema: report.schema,
  lane,
  total_python_files: report.coverage.reported_python_files,
  inventory_digest: report.coverage.inventory_digest,
  counts: report.counts,
  blockers: report.blockers,
}, null, 2));
