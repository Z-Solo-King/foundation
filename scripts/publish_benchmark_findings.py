#!/usr/bin/env python3
"""Publish deterministic benchmark/instruction findings to one tracked GitHub issue."""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Any

TRACKING_TITLE = "Nightly benchmark findings — automated tracking"
TRACKING_LABEL = "benchmark-finding"
MAX_FINDINGS = 40
MAX_DETAIL_CHARS = 600

def load_report(path: Path | None) -> dict[str, Any] | None:
    if path is None or not path.exists():
        return None
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: expected JSON object")
    return value

def collect_findings(instruction: dict[str, Any] | None, aggregate: dict[str, Any] | None) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    if instruction and int(instruction.get("finding_count") or 0) > 0:
        rows = instruction.get("findings") or []
        for row in rows:
            if isinstance(row, dict):
                findings.append({
                    "source": "instruction-audit",
                    "kind": str(row.get("kind") or "finding"),
                    "document": str(row.get("document") or "unknown"),
                    "line": str(row.get("line") or "?"),
                    "detail": str(row.get("detail") or "")[:MAX_DETAIL_CHARS],
                })
        if not findings:
            findings.append({
                "source": "instruction-audit",
                "kind": "finding-count-without-details",
                "document": "instruction-audit.json",
                "line": "?",
                "detail": f"finding_count={instruction.get("finding_count")}",
            })
    if aggregate:
        failures = aggregate.get("hard_gate_failures")
        if isinstance(failures, list):
            for item in failures[:MAX_FINDINGS]:
                findings.append({
                    "source": "aggregate-benchmark",
                    "kind": "hard-gate-failure",
                    "document": "aggregate-ai-agent-benchmark.json",
                    "line": "?",
                    "detail": str(item)[:MAX_DETAIL_CHARS],
                })
        status = str(aggregate.get("hard_gate_status") or "").upper()
        if status in {"FAIL", "FAILED", "BLOCKED"}:
            findings.append({
                "source": "aggregate-benchmark",
                "kind": "hard-gate-failure",
                "document": "aggregate-ai-agent-benchmark.json",
                "line": "?",
                "detail": f"hard_gate_status={status}",
            })
        if aggregate.get("hard_gate_failed") is True:
            findings.append({
                "source": "aggregate-benchmark",
                "kind": "hard-gate-failure",
                "document": "aggregate-ai-agent-benchmark.json",
                "line": "?",
                "detail": "hard_gate_failed=true",
            })
    return findings[:MAX_FINDINGS]

def build_issue_body(findings: list[dict[str, str]], run_id: str, repository: str) -> str:
    lines = [
        "# Automated benchmark findings",
        "",
        "Evidence tracker only. This does not authorize policy, code, deployment, or runtime changes.",
        "",
        f"- Repository: {repository}",
        f"- Workflow run: {run_id}",
        f"- Finding count: {len(findings)}",
        "",
        "## Findings",
    ]
    for index, item in enumerate(findings, 1):
        lines.append(f"{index}. {item["source"]} / {item["kind"]} - {item["document"]}:{item["line"]} - {item["detail"]}")
    lines.extend([
        "",
        "## Required path",
        "",
        "Observation -> independent reproduction -> regression fixture -> reviewed implementation/agent improvement -> repeated benchmark -> runtime evidence when required.",
    ])
    return "\n".join(lines) + "\n"

def gh(args: list[str]) -> str:
    return subprocess.run(["gh", *args], check=True, capture_output=True, text=True).stdout.strip()

def ensure_label() -> None:
    rows = json.loads(gh(["label", "list", "--search", TRACKING_LABEL, "--json", "name"]))
    if any(row.get("name") == TRACKING_LABEL for row in rows):
        return
    gh(["label", "create", TRACKING_LABEL, "--description", "Automated benchmark evidence requiring tracked follow-up", "--color", "B60205"])

def find_issue() -> int | None:
    rows = json.loads(gh(["issue", "list", "--state", "open", "--search", f"{TRACKING_TITLE} in:title", "--limit", "20", "--json", "number,title"]))
    exact = [row for row in rows if row.get("title") == TRACKING_TITLE]
    if len(exact) > 1:
        raise RuntimeError("multiple open benchmark tracking issues exist")
    return int(exact[0]["number"]) if exact else None

def publish(body: str) -> None:
    ensure_label()
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".md", delete=False) as handle:
        handle.write(body)
        path = handle.name
    try:
        number = find_issue()
        if number is None:
            gh(["issue", "create", "--title", TRACKING_TITLE, "--label", TRACKING_LABEL, "--body-file", path])
        else:
            gh(["issue", "edit", str(number), "--body-file", path])
    finally:
        Path(path).unlink(missing_ok=True)

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--instruction-report", type=Path, required=True)
    parser.add_argument("--aggregate-report", type=Path)
    args = parser.parse_args()
    instruction = load_report(args.instruction_report)
    aggregate = load_report(args.aggregate_report)
    findings = collect_findings(instruction, aggregate)
    print(json.dumps({"schema": "benchmark-finding-consumer/v1", "finding_count": len(findings)}))
    if not findings:
        return 0
    publish(build_issue_body(findings, os.environ.get("GITHUB_RUN_ID", "unknown"), os.environ.get("GITHUB_REPOSITORY", "unknown")))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
