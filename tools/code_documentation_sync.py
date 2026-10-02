#!/usr/bin/env python3
"""Validate code-to-document synchronization maps."""
from __future__ import annotations

import argparse
import fnmatch
import json
import subprocess
from pathlib import Path


MAP_REL = Path("docs/CODE_DOCUMENTATION_SYNC_MAP.json")


def git_lines(root: Path, *args: str) -> list[str]:
    result = subprocess.run(["git", *args], cwd=root, check=True, capture_output=True, text=True)
    return [x for x in result.stdout.splitlines() if x]


def tracked(root: Path) -> list[str]:
    result = subprocess.run(["git", "ls-files", "-z"], cwd=root, check=True, capture_output=True)
    return [x for x in result.stdout.decode().split("\0") if x]


def changed(root: Path, base: str) -> list[str]:
    return git_lines(root, "diff", "--name-only", f"{base}...HEAD")


def matches(path: str, pattern: str) -> bool:
    p = path.replace("\\", "/")
    pat = pattern.replace("\\", "/")
    if pat.endswith("/**"):
        return p.startswith(pat[:-3])
    return fnmatch.fnmatchcase(p, pat) or Path(p).match(pat)


def validate(root: Path, changed_paths: set[str] | None = None, strict: bool = False) -> dict[str, object]:
    tracked_files = tracked(root)
    tracked_set = set(tracked_files)
    data = json.loads((root / MAP_REL).read_text(encoding="utf-8"))
    if data.get("schema_version") != "code-doc-sync/v1":
        raise ValueError("unsupported code-doc-sync schema")
    groups = data.get("groups")
    if not isinstance(groups, list):
        raise ValueError("groups must be a list")

    issues: list[dict[str, object]] = []
    seen_ids: set[str] = set()
    rows = []
    for group in groups:
        gid = str(group.get("id", ""))
        if not gid or gid in seen_ids:
            issues.append({"rule": "unique-group-id", "group": gid, "severity": "error"})
            continue
        seen_ids.add(gid)
        code_paths = group.get("code_paths") or []
        docs = group.get("docs") or []
        if not code_paths or not docs:
            issues.append({"rule": "nonempty-group", "group": gid, "severity": "error"})
            continue
        missing_docs = [doc for doc in docs if doc not in tracked_set]
        if missing_docs:
            issues.append({"rule": "mapped-document-missing", "group": gid, "paths": missing_docs, "severity": "error"})
        matched_code = [p for p in tracked_files if any(matches(p, pat) for pat in code_paths)]
        if not matched_code:
            issues.append({"rule": "code-pattern-no-match", "group": gid, "severity": "error"})
        changed_code = [p for p in (changed_paths or set()) if any(matches(p, pat) for pat in code_paths)]
        changed_docs = [p for p in (changed_paths or set()) if p in docs]
        needs_docs = bool(group.get("require_doc_update", False)) and bool(changed_code)
        if needs_docs and not changed_docs:
            issues.append({
                "rule": "code-change-missing-documentation",
                "group": gid,
                "changed_code_count": len(changed_code),
                "severity": "error",
            })
        rows.append({
            "id": gid,
            "matched_code_count": len(matched_code),
            "changed_code_count": len(changed_code),
            "changed_doc_count": len(changed_docs),
            "require_doc_update": bool(group.get("require_doc_update", False)),
        })

    return {
        "schema_version": "code-doc-sync-report/v1",
        "repository": root.name,
        "groups": rows,
        "issues": issues,
        "passed": not any(item.get("severity") == "error" for item in issues),
        "strict": strict,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--changed-from")
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--report", type=Path)
    parser.add_argument("--summary-only", action="store_true")
    args = parser.parse_args()

    root = args.root.resolve()
    changed_paths = None
    if args.changed_from and not args.all:
        changed_paths = set(changed(root, args.changed_from))
    report = validate(root, changed_paths=changed_paths, strict=args.strict)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if args.summary_only:
        print(json.dumps({
            "groups": len(report["groups"]),
            "issues": len(report["issues"]),
            "passed": report["passed"],
        }, sort_keys=True))
    else:
        print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if (report["passed"] or not args.strict) else 1


if __name__ == "__main__":
    raise SystemExit(main())
