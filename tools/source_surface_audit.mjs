#!/usr/bin/env node
/** Report oversized source surfaces and decomposition candidates. */
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const SKIP = new Set(["__pycache__", ".git", "node_modules", "dist", "build", "target"]);
const TEXT = new Set([
  ".py",
  ".pyi",
  ".js",
  ".mjs",
  ".ts",
  ".tsx",
  ".go",
  ".rs",
  ".java",
  ".kt",
  ".swift",
  ".c",
  ".cc",
  ".cpp",
  ".cxx",
  ".h",
  ".hpp",
  ".zig",
  ".php",
  ".sh",
  ".bash",
  ".ps1",
  ".sql",
  ".yml",
  ".yaml",
  ".toml",
]);
function args(argv) {
  const out = {};
  for (let i = 0; i < argv.length; i++) {
    if (argv[i] === "--root") {
      (out.root ??= []).push(argv[++i]);
    } else if (argv[i] === "--output") {
      out.output = argv[++i];
    } else if (argv[i] === "--critical-bytes") {
      out.criticalBytes = Number(argv[++i]);
    } else if (argv[i] === "--critical-lines") {
      out.criticalLines = Number(argv[++i]);
    } else if (argv[i] === "--attention-bytes") {
      out.attentionBytes = Number(argv[++i]);
    } else if (argv[i] === "--attention-lines") {
      out.attentionLines = Number(argv[++i]);
    }
  }
  return out;
}
function walk(root) {
  const out = [];
  const visit = (dir) => {
    for (const e of fs.readdirSync(dir, { withFileTypes: true })) {
      if (SKIP.has(e.name)) continue;
      const f = path.join(dir, e.name);
      if (e.isDirectory()) visit(f);
      else if (e.isFile()) out.push(f);
    }
  };
  visit(root);
  return out;
}
export function audit(roots, thresholds = {}) {
  const criticalBytes = Number(thresholds.criticalBytes ?? 50000),
    criticalLines = Number(thresholds.criticalLines ?? 1000);
  const attentionBytes = Number(thresholds.attentionBytes ?? 25000),
    attentionLines = Number(thresholds.attentionLines ?? 500);
  const rows = [];
  for (const raw of roots) {
    const root = path.resolve(raw),
      repo = path.basename(root);
    for (const file of walk(root)) {
      if (!TEXT.has(path.extname(file).toLowerCase())) continue;
      const text = fs.readFileSync(file, "utf8");
      const bytes = Buffer.byteLength(text, "utf8"),
        lines = text.length ? text.split("\n").length : 1;
      const severity =
        bytes > criticalBytes || lines > criticalLines
          ? "critical"
          : bytes > attentionBytes || lines > attentionLines
            ? "attention"
            : "normal";
      if (severity !== "normal") {
        const rel = path.relative(root, file).replaceAll("\\", "/");
        rows.push({
          repo,
          path: rel,
          bytes,
          lines,
          severity,
          generated_or_historical:
            rel.includes("docs/HISTORY/") ||
            rel.includes("docs/history/") ||
            rel.includes("/runtime-evidence/"),
        });
      }
    }
  }
  rows.sort(
    (a, b) =>
      Number(b.severity !== "critical") - Number(a.severity !== "critical") ||
      b.bytes - a.bytes ||
      b.lines - a.lines ||
      a.repo.localeCompare(b.repo) ||
      a.path.localeCompare(b.path),
  );
  return {
    schema: "source-surface-audit/v1",
    critical_thresholds: { bytes: criticalBytes, lines: criticalLines },
    attention_thresholds: { bytes: attentionBytes, lines: attentionLines },
    rows,
    critical_code_count: rows.filter((x) => x.severity === "critical" && !x.generated_or_historical)
      .length,
    attention_code_count: rows.filter(
      (x) => x.severity === "attention" && !x.generated_or_historical,
    ).length,
  };
}
if (fileURLToPath(import.meta.url) === process.argv[1]) {
  const a = args(process.argv.slice(2));
  if (!a.root?.length || !a.output)
    throw new Error("--root (repeatable) and --output are required");
  const result = audit(a.root, a);
  fs.mkdirSync(path.dirname(path.resolve(a.output)), { recursive: true });
  fs.writeFileSync(path.resolve(a.output), JSON.stringify(result, null, 2) + "\n");
  console.log(
    JSON.stringify(
      {
        schema: result.schema,
        critical_code_count: result.critical_code_count,
        attention_code_count: result.attention_code_count,
      },
      null,
      2,
    ),
  );
}
