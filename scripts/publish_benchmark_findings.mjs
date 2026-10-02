#!/usr/bin/env node
/** Publish deterministic benchmark/instruction findings to one tracked GitHub issue. */
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { execFileSync } from "node:child_process";
import { fileURLToPath } from "node:url";

export const TRACKING_TITLE = "Nightly benchmark findings — automated tracking";
export const TRACKING_LABEL = "benchmark-finding";
const MAX_FINDINGS = 40;
const MAX_DETAIL_CHARS = 600;

export function loadReport(filePath) {
  if (!filePath || !fs.existsSync(filePath)) return null;
  const value = JSON.parse(fs.readFileSync(filePath, "utf8"));
  if (!value || typeof value !== "object" || Array.isArray(value)) {
    throw new Error(filePath + ": expected JSON object");
  }
  return value;
}

export function collectFindings(instruction, aggregate) {
  const findings = [];

  if (instruction && Number(instruction.finding_count || 0) > 0) {
    const rows = Array.isArray(instruction.findings) ? instruction.findings : [];
    for (const row of rows) {
      if (row && typeof row === "object") {
        findings.push({
          source: "instruction-audit",
          kind: String(row.kind || "finding"),
          document: String(row.document || "unknown"),
          line: String(row.line || "?"),
          detail: String(row.detail || "").slice(0, MAX_DETAIL_CHARS),
        });
      }
    }
    if (!findings.length) {
      findings.push({
        source: "instruction-audit",
        kind: "finding-count-without-details",
        document: "instruction-audit.json",
        line: "?",
        detail: "finding_count=" + String(instruction.finding_count),
      });
    }
  }

  if (aggregate && Array.isArray(aggregate.hard_gate_failures)) {
    for (const item of aggregate.hard_gate_failures.slice(0, MAX_FINDINGS)) {
      findings.push({
        source: "aggregate-benchmark",
        kind: "hard-gate-failure",
        document: "aggregate-ai-agent-benchmark.json",
        line: "?",
        detail: String(item).slice(0, MAX_DETAIL_CHARS),
      });
    }
  }

  const status = String(aggregate?.hard_gate_status || "").toUpperCase();
  if (["FAIL", "FAILED", "BLOCKED"].includes(status)) {
    findings.push({
      source: "aggregate-benchmark",
      kind: "hard-gate-failure",
      document: "aggregate-ai-agent-benchmark.json",
      line: "?",
      detail: "hard_gate_status=" + status,
    });
  }

  if (aggregate?.hard_gate_failed === true) {
    findings.push({
      source: "aggregate-benchmark",
      kind: "hard-gate-failure",
      document: "aggregate-ai-agent-benchmark.json",
      line: "?",
      detail: "hard_gate_failed=true",
    });
  }

  return findings.slice(0, MAX_FINDINGS);
}

export function buildIssueBody(findings, runId, repository) {
  const lines = [
    "# Automated benchmark findings",
    "",
    "Evidence tracker only. This does not authorize policy, code, deployment, or runtime changes.",
    "",
    "- Repository: " + repository,
    "- Workflow run: " + runId,
    "- Finding count: " + String(findings.length),
    "",
    "## Findings",
  ];
  findings.forEach((item, index) => {
    lines.push(
      String(index + 1) + ". " + item.source + " / " + item.kind +
      " - " + item.document + ":" + item.line + " - " + item.detail,
    );
  });
  lines.push(
    "",
    "## Required path",
    "",
    "Observation -> independent reproduction -> regression fixture -> reviewed implementation/agent improvement -> repeated benchmark -> runtime evidence when required.",
  );
  return lines.join("\n") + "\n";
}

function gh(args) {
  return execFileSync("gh", args, { encoding: "utf8" }).trim();
}

function publish(body) {
  const labelRows = JSON.parse(gh(["label", "list", "--search", TRACKING_LABEL, "--json", "name"]));
  if (!labelRows.some((row) => row?.name === TRACKING_LABEL)) {
    gh([
      "label", "create", TRACKING_LABEL,
      "--description", "Automated benchmark evidence requiring tracked follow-up",
      "--color", "B60205",
    ]);
  }

  const rows = JSON.parse(gh([
    "issue", "list", "--state", "open",
    "--search", TRACKING_TITLE + " in:title",
    "--limit", "20", "--json", "number,title",
  ]));
  const exact = rows.filter((row) => row?.title === TRACKING_TITLE);
  if (exact.length > 1) throw new Error("multiple open benchmark tracking issues exist");

  const filePath = path.join(os.tmpdir(), "heroic-benchmark-" + process.pid + ".md");
  fs.writeFileSync(filePath, body, { encoding: "utf8", mode: 0o600 });
  try {
    if (!exact.length) {
      gh(["issue", "create", "--title", TRACKING_TITLE, "--label", TRACKING_LABEL, "--body-file", filePath]);
    } else {
      gh(["issue", "edit", String(exact[0].number), "--body-file", filePath]);
    }
  } finally {
    fs.rmSync(filePath, { force: true });
  }
}

function parseArgs(argv) {
  const out = {};
  for (let i = 0; i < argv.length; i += 1) {
    if (argv[i].startsWith("--")) {
      out[argv[i].slice(2)] = argv[i + 1] ?? "";
      i += 1;
    }
  }
  return out;
}

if (process.argv[1] && fileURLToPath(import.meta.url) === process.argv[1]) {
  const args = parseArgs(process.argv.slice(2));
  const findings = collectFindings(
    loadReport(args["instruction-report"]),
    loadReport(args["aggregate-report"]),
  );
  process.stdout.write(JSON.stringify({
    schema: "benchmark-finding-consumer/v1",
    finding_count: findings.length,
  }) + "\n");
  if (findings.length) {
    publish(buildIssueBody(
      findings,
      process.env.GITHUB_RUN_ID || "unknown",
      process.env.GITHUB_REPOSITORY || "unknown",
    ));
  }
}
