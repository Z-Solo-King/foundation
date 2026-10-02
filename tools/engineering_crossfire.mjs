#!/usr/bin/env node
/**
 * Repository-wide deterministic CrossFire scanner.
 *
 * Responsibility:
 *   Run six independent read-only diagnostics over a frozen repository snapshot.
 *
 * Non-responsibility:
 *   No source mutation, policy mutation, promotion, deployment or authority transfer.
 */
import fs from "node:fs";
import path from "node:path";
import crypto from "node:crypto";

const ROOT = process.cwd();
const PROFILE_PATH = path.join(ROOT, "docs", "ENGINEERING_CROSSFIRE_PROFILE.json");
const EXCLUDES = new Set([".git", "node_modules", ".venv", "venv", "__pycache__", ".pytest_cache", ".runtime"]);

function parseArgs(argv) {
  const args = { operationsRoot: "", output: "", maxFiles: 20000 };
  for (let i = 0; i < argv.length; i += 1) {
    if (argv[i] === "--operations-root") args.operationsRoot = argv[++i] || "";
    else if (argv[i] === "--output") args.output = argv[++i] || "";
    else if (argv[i] === "--max-files") args.maxFiles = Number(argv[++i] || 20000);
  }
  return args;
}

function sha256(value) {
  return crypto.createHash("sha256").update(value).digest("hex");
}

function readJson(file) {
  return JSON.parse(fs.readFileSync(file, "utf8"));
}

function relFiles(root, maxFiles) {
  const out = [];
  function visit(dir) {
    if (out.length >= maxFiles) return;
    for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
      if (EXCLUDES.has(entry.name)) continue;
      const full = path.join(dir, entry.name);
      if (entry.isDirectory()) visit(full);
      else if (entry.isFile()) out.push(path.relative(root, full).replaceAll(path.sep, "/"));
      if (out.length >= maxFiles) break;
    }
  }
  visit(root);
  return out.sort();
}

function readText(root, rel) {
  try {
    return fs.readFileSync(path.join(root, rel), "utf8");
  } catch {
    return "";
  }
}

function makeFinding(lane, code, severity, subject, message, extra = {}) {
  return { lane, code, severity, subject, message, ...extra };
}

function ownershipLane(snapshot) {
  const findings = [];
  if (!snapshot.operationsRoot) {
    findings.push(makeFinding("ownership", "operations-scan-unavailable", "warning", "operations", "Private Operations checkout was not supplied; cross-repository duplicate-source detection is unavailable."));
    return findings;
  }
  const foundationFiles = relFiles(snapshot.root, snapshot.maxFiles);
  const operationsFiles = new Set(relFiles(snapshot.operationsRoot, snapshot.maxFiles));
  const roots = new Set(["backend", "foundation_core", "execution", "polyglot", "private", "extractor_mapper"]);
  for (const rel of foundationFiles) {
    const top = rel.split("/")[0];
    if (!roots.has(top) && rel !== "worker.py" && rel !== "edge.ts") continue;
    if (!operationsFiles.has(rel)) continue;
    const a = readText(snapshot.root, rel);
    const b = readText(snapshot.operationsRoot, rel);
    if (a && a.length >= 400 && a === b) {
      findings.push(makeFinding("ownership", "identical-cross-repo-source", "error", rel, "Identical substantial source exists in both repositories; confirm one canonical implementation owner.", { size: a.length, digest: sha256(a) }));
    }
  }
  return findings;
}

function contractsLane(snapshot) {
  const findings = [];
  const required = [
    "AGENTS.md",
    "REPOSITORY_MAP.json",
    "docs/FAMILY_SYNC_STATE.json",
    "docs/ENGINEERING_CROSSFIRE_PROFILE.json"
  ];
  for (const rel of required) {
    if (!fs.existsSync(path.join(snapshot.root, rel))) {
      findings.push(makeFinding("contracts", "required-surface-missing", "error", rel, "Required navigation or machine-contract surface is missing."));
    }
  }
  for (const rel of ["REPOSITORY_MAP.json", "docs/FAMILY_SYNC_STATE.json", "docs/ENGINEERING_CROSSFIRE_PROFILE.json"]) {
    const p = path.join(snapshot.root, rel);
    if (!fs.existsSync(p)) continue;
    try {
      readJson(p);
    } catch (error) {
      findings.push(makeFinding("contracts", "invalid-json-contract", "error", rel, "Machine-readable contract is not valid JSON.", { error_class: error.name }));
    }
  }
  if (snapshot.operationsRoot && !fs.existsSync(path.join(snapshot.operationsRoot, "REPOSITORY_MAP.json"))) {
    findings.push(makeFinding("contracts", "operations-map-missing", "warning", "operations/REPOSITORY_MAP.json", "Operations repository map was not found."));
  }
  return findings;
}

function workflowsLane(snapshot) {
  const findings = [];
  const dir = path.join(snapshot.root, ".github", "workflows");
  const files = fs.existsSync(dir) ? fs.readdirSync(dir).filter(x => x.endsWith(".yml") || x.endsWith(".yaml")).sort() : [];
  if (!files.length) findings.push(makeFinding("workflows", "no-foundation-workflows", "error", ".github/workflows", "No Foundation workflow files were discovered."));
  if (snapshot.operationsRoot && fs.existsSync(path.join(snapshot.operationsRoot, ".github", "workflows"))) {
    const count = relFiles(path.join(snapshot.operationsRoot, ".github", "workflows"), snapshot.maxFiles).length;
    if (count > 0) findings.push(makeFinding("workflows", "competing-operations-workflows", "error", "operations/.github/workflows", "Operations contains workflow files even though Foundation is the hosted CI authority.", { count }));
  }
  return findings;
}

function languageLane(snapshot) {
  const counts = new Map();
  for (const rel of relFiles(snapshot.root, snapshot.maxFiles)) {
    const ext = path.extname(rel).toLowerCase() || "[none]";
    counts.set(ext, (counts.get(ext) || 0) + 1);
  }
  const expected = new Set([".py", ".js", ".mjs", ".ts", ".tsx", ".json", ".yml", ".yaml", ".md", ".css", ".html", ".rs", ".go", ".toml", ".sh", ".txt", ".lock", ".svg", ".map"]);
  return [...counts.entries()]
    .filter(([ext]) => ext !== "[none]" && !expected.has(ext))
    .sort()
    .map(([ext, count]) => makeFinding("language", "unexpected-source-extension", "warning", ext, "Source extension is outside the maintained default toolchain inventory; verify intentional ownership and tooling.", { count }));
}

function documentationLane(snapshot) {
  const findings = [];
  const today = new Date();
  for (const rel of relFiles(snapshot.root, snapshot.maxFiles).filter(x => x.startsWith("docs/") && /20\\d{2}-\\d{2}-\\d{2}/.test(x))) {
    const m = rel.match(/(20\\d{2})-(\\d{2})-(\\d{2})/);
    const date = new Date(Date.UTC(Number(m[1]), Number(m[2]) - 1, Number(m[3])));
    const age = Math.floor((today.getTime() - date.getTime()) / 86400000);
    if (age >= 14) findings.push(makeFinding("documentation", "dated-doc-review", "warning", rel, "Dated operational documentation is at least 14 days old and requires source-of-truth review.", { age_days: age }));
  }
  return findings;
}

function publicSurfaceLane(snapshot) {
  const findings = [];
  const files = relFiles(snapshot.root, snapshot.maxFiles).filter(rel =>
    rel.startsWith("docs/") || rel.startsWith("frontend/") || rel === "worker.py" || rel === "edge.ts"
  );
  const patterns = [
    [/BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY/i, "credential-like-private-key"],
    [/(ghp_|github_pat_)[A-Za-z0-9_]+/i, "github-token-like"],
    [/operations\\/private\\//i, "private-runtime-path"],
    [/CLOUDFLARE_API_TOKEN|OPERATIONS_APP_PRIVATE_KEY|PROVIDER_KEYS_JSON/i, "secret-name-exposure"]
  ];
  for (const rel of files) {
    const source = readText(snapshot.root, rel);
    for (const [regex, code] of patterns) {
      if (regex.test(source)) findings.push(makeFinding("public-surface", code, "error", rel, "High-confidence sensitive/private marker detected in the public repository surface."));
    }
  }
  return findings;
}

const args = parseArgs(process.argv.slice(2));
const profile = readJson(PROFILE_PATH);
const snapshot = {
  root: ROOT,
  operationsRoot: args.operationsRoot ? path.resolve(args.operationsRoot) : "",
  maxFiles: Math.max(100, args.maxFiles)
};

const lanes = [
  ["ownership", () => ownershipLane(snapshot)],
  ["contracts", () => contractsLane(snapshot)],
  ["workflows", () => workflowsLane(snapshot)],
  ["language", () => languageLane(snapshot)],
  ["documentation", () => documentationLane(snapshot)],
  ["public-surface", () => publicSurfaceLane(snapshot)]
];

const started = Date.now();
const results = await Promise.all(lanes.map(async ([id, run]) => {
  const laneStarted = Date.now();
  try {
    const findings = run();
    return { id, status: "completed", duration_ms: Date.now() - laneStarted, findings };
  } catch (error) {
    return {
      id,
      status: "unavailable",
      duration_ms: Date.now() - laneStarted,
      findings: [makeFinding(id, "lane-error", "error", id, "Lane failed; unrelated lanes continue.", { error_class: error?.name || "Error" })]
    };
  }
}));

const completed = results.filter(x => x.status === "completed").length;
const findings = results.flatMap(x => x.findings);
const grouped = new Map();
for (const item of findings) {
  const key = item.code + "::" + item.subject;
  if (!grouped.has(key)) grouped.set(key, []);
  grouped.get(key).push(item);
}
const agreement = [...grouped.entries()]
  .filter(([, rows]) => new Set(rows.map(x => x.lane)).size >= 2)
  .map(([key, rows]) => ({ key, lanes: [...new Set(rows.map(x => x.lane))].sort() }));

const strength = completed === 6 ? "full_6" : completed >= 5 ? "strong_5" : completed >= 2 ? "limited" : "insufficient";
const receipt = {
  schema: "engineering-crossfire-receipt/v1",
  generated_at: new Date().toISOString(),
  authority: "diagnostic_only",
  input: {
    foundation_root: ".",
    operations_root: snapshot.operationsRoot ? "private-operations-checkout" : null,
    foundation_tree_digest: sha256(relFiles(snapshot.root, snapshot.maxFiles).join("\\n")),
    file_cap: snapshot.maxFiles
  },
  profile: {
    schema: profile.schema,
    required_lanes: profile.required_lanes,
    max_lanes: profile.max_lanes
  },
  crossfire: {
    strength,
    lanes_expected: 6,
    lanes_completed: completed,
    parallel: true,
    shared_lane_feedback: false,
    mutation_phase: "separate"
  },
  lanes: results.map(x => ({
    id: x.id,
    status: x.status,
    duration_ms: x.duration_ms,
    finding_count: x.findings.length,
    finding_digest: sha256(JSON.stringify(x.findings))
  })),
  findings,
  comparisons: {
    multi_lane_agreement: agreement,
    disagreement: [],
    interpretation: "Agreement is diagnostic evidence only; deterministic policy and tests remain authoritative."
  },
  summary: {
    total_findings: findings.length,
    errors: findings.filter(x => x.severity === "error").length,
    warnings: findings.filter(x => x.severity === "warning").length,
    infos: findings.filter(x => x.severity === "info").length,
    wall_ms: Date.now() - started
  }
};

const output = args.output ? path.resolve(args.output) : path.join(ROOT, ".runtime", "engineering-crossfire.json");
fs.mkdirSync(path.dirname(output), { recursive: true });
fs.writeFileSync(output, JSON.stringify(receipt, null, 2) + "\\n");
process.stdout.write(JSON.stringify({
  schema: receipt.schema,
  strength: receipt.crossfire.strength,
  lanes_completed: receipt.crossfire.lanes_completed,
  findings: receipt.summary.total_findings,
  errors: receipt.summary.errors,
  warnings: receipt.summary.warnings
}, null, 2) + "\\n");
