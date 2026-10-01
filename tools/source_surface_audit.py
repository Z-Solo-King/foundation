#!/usr/bin/env python3
"""Report oversized source surfaces and optionally fail on critical code."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

SKIP={"__pycache__", ".git", "node_modules", "dist", "build", "target"}
TEXT={".py",".pyi",".js",".mjs",".ts",".tsx",".go",".rs",".java",".kt",".swift",".c",".cc",".cpp",".cxx",".h",".hpp",".zig",".php",".sh",".bash",".ps1",".sql",".yml",".yaml",".toml"}


def iter_sources(root: Path):
    for path in root.rglob("*"):
        if not path.is_file() or any(part in SKIP for part in path.parts) or path.suffix.lower() not in TEXT:
            continue
        text=path.read_text(encoding="utf-8", errors="ignore")
        yield path, len(text.encode("utf-8")), text.count("\n")+1


def main() -> int:
    parser=argparse.ArgumentParser()
    parser.add_argument("--root", action="append", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--critical-bytes", type=int, default=50000)
    parser.add_argument("--critical-lines", type=int, default=1000)
    parser.add_argument("--attention-bytes", type=int, default=25000)
    parser.add_argument("--attention-lines", type=int, default=500)
    parser.add_argument("--fail-critical-code", action="store_true")
    args=parser.parse_args()

    rows=[]
    for raw in args.root:
        root=Path(raw).resolve()
        repo=root.name
        for path,bytes_,lines in iter_sources(root):
            rel=str(path.relative_to(root)).replace("\\","/")
            historical=rel.startswith("docs/HISTORY/") or "/runtime-evidence/" in f"/{rel}"
            severity="critical" if bytes_>args.critical_bytes or lines>args.critical_lines else "attention" if bytes_>args.attention_bytes or lines>args.attention_lines else "normal"
            if severity!="normal":
                rows.append({
                    "repo":repo,"path":rel,"bytes":bytes_,"lines":lines,
                    "severity":severity,"generated_or_historical":historical,
                    "decomposition_required":severity=="critical" and not historical,
                })

    rows.sort(key=lambda x:(x["severity"]!="critical",-x["bytes"],-x["lines"],x["repo"],x["path"]))
    critical_code=[x for x in rows if x["severity"]=="critical" and not x["generated_or_historical"]]
    attention_code=[x for x in rows if x["severity"]=="attention" and not x["generated_or_historical"]]
    result={
        "schema":"source-surface-audit/v2",
        "critical_thresholds":{"bytes":args.critical_bytes,"lines":args.critical_lines},
        "attention_thresholds":{"bytes":args.attention_bytes,"lines":args.attention_lines},
        "rows":rows,
        "critical_code_count":len(critical_code),
        "attention_code_count":len(attention_code),
        "largest_attention_code":attention_code[:20],
        "status":"PASS" if not critical_code else "FAIL",
    }
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({k:result[k] for k in ("schema","critical_code_count","attention_code_count","status")},indent=2))
    if args.fail_critical_code and critical_code:
        return 1
    return 0


if __name__=="__main__":
    raise SystemExit(main())
