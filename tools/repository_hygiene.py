#!/usr/bin/env python3
"""Repository hygiene and uniform-format gate.

The checker is intentionally dependency-light. Language-specific formatting is
delegated to pinned Ruff/Prettier/markdownlint-cli2 commands when --format-check
is requested.
"""
from __future__ import annotations

import argparse
import fnmatch
import json
import re
import subprocess
from pathlib import Path
from typing import Iterable

CONTRACT_REL = Path("docs/REPOSITORY_HYGIENE_FORMAT_CONTRACT.json")
TEXT_EXTENSIONS = {
    ".cjs", ".css", ".html", ".json", ".jsonc", ".mjs", ".md", ".py",
    ".scss", ".ts", ".tsx", ".toml", ".txt", ".yml", ".yaml",
}
FORMATTER_EXTENSIONS = {
    ".cjs", ".json", ".jsonc", ".js", ".mjs", ".md", ".py", ".ts", ".tsx", ".yaml", ".yml"
}
FORBIDDEN_TRACKED = (
    "__pycache__/", ".coverage", ".pytest_cache/", "coverage.xml",
    "htmlcov/", "node_modules/", ".DS_Store",
)
DATE_NAME_RE = re.compile(r"(?:19|20)\\d{2}[-_]\\d{2}[-_]\\d{2}")
TAB_RE = re.compile(r"^\\t+")


def run_git(root: Path, *args: str) -> list[str]:
    result = subprocess.run(
        ["git", *args],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    )
    return [item for item in result.stdout.splitlines() if item]


def tracked_files(root: Path) -> list[str]:
    result = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=root,
        check=True,
        capture_output=True,
    )
    return [
        item for item in result.stdout.decode("utf-8").split("\0") if item
    ]


def changed_files(root: Path, base: str) -> list[str]:
    return run_git(root, "diff", "--name-only", f"{base}...HEAD")


def normalize_selection(root: Path, all_files: bool, base: str | None) -> tuple[list[str], bool]:
    files = tracked_files(root)
    if all_files:
        return files, False
    if base:
        return [path for path in changed_files(root, base) if path in set(files)], True
    return files, False


def is_text_path(path: str) -> bool:
    return Path(path).suffix.lower() in TEXT_EXTENSIONS or Path(path).name in {"AGENTS.md", "README.md"}


def is_formatter_path(path: str) -> bool:
    return Path(path).suffix.lower() in FORMATTER_EXTENSIONS


def is_forbidden_artifact(path: str) -> bool:
    normalized = path.replace("\\", "/")
    return any(token in normalized or normalized.endswith(token) for token in FORBIDDEN_TRACKED)


def check_bytes(full_path: Path, relative: str) -> list[dict[str, object]]:
    raw = full_path.read_bytes()
    issues: list[dict[str, object]] = []
    if b"\x00" in raw:
        return [{"rule": "binary-control", "path": relative, "severity": "error"}]
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        return [{"rule": "utf8", "path": relative, "severity": "error"}]
    if "\r\n" in text or "\r" in text:
        issues.append({"rule": "lf-only", "path": relative, "severity": "error"})
    if raw and not raw.endswith(b"\n"):
        issues.append({"rule": "final-newline", "path": relative, "severity": "error"})
    if any(re.search(r"[ \\t]+$", line) for line in text.splitlines()):
        issues.append({"rule": "trailing-whitespace", "path": relative, "severity": "error"})
    if any(TAB_RE.search(line) for line in text.splitlines()):
        issues.append({"rule": "tab-indentation", "path": relative, "severity": "error"})
    return issues


def check_markdown_name(relative: str) -> list[dict[str, object]]:
    path = Path(relative)
    if path.suffix.lower() != ".md":
        return []
    normalized = relative.replace("\\", "/")
    allowed = ("docs/history/", "docs/HISTORY/", "docs/feed-lab/", "docs/runtime/")
    if DATE_NAME_RE.search(path.name) and not normalized.startswith(allowed):
        return [{
            "rule": "date-named-canonical-doc",
            "path": relative,
            "severity": "error",
        }]
    return []


def check_size(full_path: Path, relative: str, changed_mode: bool) -> list[dict[str, object]]:
    if Path(relative).suffix.lower() not in {".py", ".js", ".mjs", ".cjs", ".ts", ".tsx"}:
        return []
    lines = full_path.read_text(encoding="utf-8", errors="replace").splitlines()
    if len(lines) <= 1000 and full_path.stat().st_size <= 50000:
        return []
    return [{
        "rule": "critical-source-size",
        "path": relative,
        "severity": "error" if changed_mode else "warning",
    }]


def build_report(root: Path, selected: Iterable[str], changed_mode: bool) -> dict[str, object]:
    violations: list[dict[str, object]] = []
    counts = {"files_checked": 0, "files_with_errors": 0, "warnings": 0}
    selected_list = list(selected)
    for relative in selected_list:
        full = root / relative
        if not full.is_file():
            continue
        counts["files_checked"] += 1
        file_issues: list[dict[str, object]] = []
        if is_text_path(relative):
            file_issues.extend(check_bytes(full, relative))
        if is_forbidden_artifact(relative):
            file_issues.append({"rule": "tracked-artifact", "path": relative, "severity": "error"})
        file_issues.extend(check_markdown_name(relative))
        file_issues.extend(check_size(full, relative, changed_mode))
        violations.extend(file_issues)
    counts["files_with_errors"] = len({item["path"] for item in violations if item["severity"] == "error"})
    counts["warnings"] = sum(item["severity"] == "warning" for item in violations)
    return {
        "schema_version": "repository-hygiene-report/v1",
        "repository": root.name,
        "mode": "changed" if changed_mode else "all",
        "files": counts,
        "violations": violations,
        "passed": not any(item["severity"] == "error" for item in violations),
    }


def run_formatter(root: Path, selected: list[str]) -> list[dict[str, object]]:
    py = [p for p in selected if Path(p).suffix == ".py"]
    prettier = [p for p in selected if Path(p).suffix.lower() in {".js", ".mjs", ".cjs", ".ts", ".tsx", ".json", ".jsonc", ".md", ".yml", ".yaml"}]
    markdown = [p for p in selected if Path(p).suffix.lower() == ".md"]
    commands: list[tuple[list[str], str]] = []
    if py:
        commands.append((["ruff", "format", "--check", *py], "ruff-format"))
        commands.append((["ruff", "check", *py], "ruff-lint"))
    if prettier:
        commands.append((["npx", "--yes", "prettier@3.9.9", "--check", *prettier], "prettier"))
    if markdown:
        commands.append((["npx", "--yes", "markdownlint-cli2@0.23.3", *markdown], "markdownlint"))
    failures: list[dict[str, object]] = []
    for command, rule in commands:
        result = subprocess.run(command, cwd=root, capture_output=True, text=True)
        if result.returncode:
            failures.append({
                "rule": rule,
                "severity": "error",
                "path": "<formatter>",
                "exit_code": result.returncode,
                "output": (result.stdout + result.stderr).strip()[-2000:],
            })
    return failures


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--changed-from")
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--format-check", action="store_true")
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--report", type=Path)
    parser.add_argument("--summary-only", action="store_true")
    args = parser.parse_args()

    root = args.root.resolve()
    contract_path = root / CONTRACT_REL
    if not contract_path.is_file():
        raise SystemExit(f"missing hygiene contract: {CONTRACT_REL}")
    json.loads(contract_path.read_text(encoding="utf-8"))

    files, changed_mode = normalize_selection(root, args.all, args.changed_from)
    report = build_report(root, files, changed_mode)
    if args.format_check:
        report["violations"].extend(run_formatter(root, [p for p in files if is_formatter_path(p)]))
        report["passed"] = report["passed"] and not any(v["severity"] == "error" for v in report["violations"])

    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    if args.summary_only:
        summary = dict(report["files"])
        summary["passed"] = report["passed"]
        print(json.dumps(summary, sort_keys=True))
    else:
        print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if (report["passed"] or not args.strict) else 1


if __name__ == "__main__":
    raise SystemExit(main())
