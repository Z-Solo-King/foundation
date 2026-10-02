#!/usr/bin/env node
import { execFileSync } from "node:child_process";
import { readFileSync, writeFileSync } from "node:fs";
import { join } from "node:path";

const args = new Map();
for (let i = 2; i < process.argv.length; i++) {
  const k = process.argv[i];
  if (k.startsWith("--")) args.set(k, process.argv[++i] ?? "");
}
const root = args.get("--root") || ".";
const lane = args.get("--lane") || "inventory";
const out = args.get("--out") || ".runtime/migration-factory-" + lane + ".json";

const run = (cmd, argv) => execFileSync(cmd, argv, { cwd: root, encoding: "utf8" }).trim();
const files = run("git", ["ls-files", "-z", "--", "*.py"]).split("\0").filter(Boolean);
const read = (p) => { try { return readFileSync(join(root, p), "utf8"); } catch { return ""; } };
const norm = (p) => p.replaceAll("\\", "/");

const classify = (p) => {
  const x = norm(p);
  if (/(^|\/)tests?\//.test(x) || /(^|\/)test_[^/]+\.py$/.test(x)) return "test";
  if (x.includes("/benchmark/") || x.startsWith("benchmark/")) return "benchmark";
  if (x.includes("/tools/") || x.startsWith("tools/") || x.includes("/scripts/") || x.startsWith("scripts/")) return "tooling";
  if (x.includes("/archive/") || x.includes("/history/") || x.includes("/retired/")) return "archive";
  if (x.startsWith("foundation_core/") || x.startsWith("backend/") || x.startsWith("private/") ||
      /(^|\/)(worker|foundation_worker)\.py$/.test(x) || x.startsWith("extractor_mapper/")) return "runtime";
  return "other";
};

const target = (p) => {
  const x = norm(p);
  if (/private\/(policy|resource_ledger|durable_resource_ledger|promotion|artifact_manifest|audit_provenance|replay|idempotency)/.test(x) ||
      /backend\/persistence/.test(x)) return {language:"retain-python", reason:"protected authority; requires separate authority migration"};
  if (/url|canonical/i.test(x) || /text_normalization|html_kernel|jsonld|robots|sitemap|link_pagination|product_mapping/.test(x))
    return {language:"rust", reason:"deterministic parsing/normalization/CPU-bound kernel"};
  if (/edge|sse|search|browser|endpoint|acquisition|next_data|stream/i.test(x))
    return {language:"typescript", reason:"edge/browser/search/provider boundary"};
  if (/fanout/i.test(x)) return {language:"go", reason:"bounded high-concurrency network tooling"};
  if (classify(p) === "tooling") return {language:"node-or-shell", reason:"CI/repository automation should not require Python where avoidable"};
  if (classify(p) === "test" || classify(p) === "benchmark") return {language:"follow-production-owner", reason:"verification follows migrated responsibility"};
  return {language:"review-required", reason:"no automatic target assignment"};
};

const imp = /(?:from|import)\s+([A-Za-z_][\w.]*)/g;
const rows = files.map((path) => {
  const body = read(path);
  const imports = new Set();
  for (const m of body.matchAll(imp)) imports.add(m[1]);
  const c = classify(path), t = target(path);
  return {
    path, class:c, target_language:t.language, target_reason:t.reason,
    imports:[...imports].slice(0,80),
    has_subprocess:/subprocess|os\.system|Popen/.test(body),
    has_exec_python:/python(?:3)?\s+-m|sys\.executable/.test(body),
    has_network:/requests|httpx|urllib|aiohttp/.test(body),
    has_state:/sqlite|d1|redis|kv|durable|ledger|persistence/.test(body),
    lane
  };
});
const count=(k)=>rows.reduce((a,r)=>(a[r[k]]=(a[r[k]]||0)+1,a),{});
const report={
  schema:"polyglot-migration-factory/v1",
  generated_at:new Date().toISOString(),
  repository:run("git",["remote","get-url","origin"]),
  revision:run("git",["rev-parse","HEAD"]),
  lane,total_python_files:rows.length,
  counts:{class:count("class"),target_language:count("target_language")},
  blockers:{
    python_runtime_files:rows.filter(r=>r.class==="runtime").length,
    python_tooling_files:rows.filter(r=>r.class==="tooling").length,
    python_tests_and_benchmarks:rows.filter(r=>["test","benchmark"].includes(r.class)).length,
    retained_authority_candidates:rows.filter(r=>r.target_language==="retain-python").length,
    python_subprocess_edges:rows.filter(r=>r.has_exec_python).length,
    review_required:rows.filter(r=>r.target_language==="review-required").length
  },
  files:rows
};
writeFileSync(join(root,out),JSON.stringify(report,null,2)+"\n");
console.log(JSON.stringify({schema:report.schema,lane,total_python_files:report.total_python_files,counts:report.counts,blockers:report.blockers},null,2));
