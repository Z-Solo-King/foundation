#!/usr/bin/env python3
"""Report oversized source surfaces and decomposition candidates."""
from __future__ import annotations
import argparse,json
from pathlib import Path
SKIP={"__pycache__", ".git", "node_modules", "dist", "build", "target"}
TEXT={".py",".pyi",".js",".mjs",".ts",".tsx",".go",".rs",".java",".kt",".swift",".c",".cc",".cpp",".cxx",".h",".hpp",".zig",".php",".sh",".bash",".ps1",".sql",".yml",".yaml",".toml"}

def iter_sources(root: Path):
    for path in root.rglob("*"):
        if not path.is_file() or any(p in SKIP for p in path.parts) or path.suffix.lower() not in TEXT: continue
        text=path.read_text(encoding="utf-8",errors="ignore")
        yield path,len(text.encode("utf-8")),text.count("\n")+1

def main()->int:
    p=argparse.ArgumentParser(); p.add_argument("--root",action="append",required=True); p.add_argument("--output",type=Path,required=True); p.add_argument("--critical-bytes",type=int,default=50000); p.add_argument("--critical-lines",type=int,default=1000); p.add_argument("--attention-bytes",type=int,default=25000); p.add_argument("--attention-lines",type=int,default=500)
    a=p.parse_args(); rows=[]
    for raw in a.root:
        root=Path(raw).resolve(); repo=root.name
        for path,bytes_,lines in iter_sources(root):
            severity="critical" if bytes_>a.critical_bytes or lines>a.critical_lines else "attention" if bytes_>a.attention_bytes or lines>a.attention_lines else "normal"
            if severity!="normal": rows.append({"repo":repo,"path":str(path.relative_to(root)).replace("\\","/"),"bytes":bytes_,"lines":lines,"severity":severity,"generated_or_historical":("docs/HISTORY/" in str(path.relative_to(root)).replace("\\","/") or "/runtime-evidence/" in str(path.relative_to(root)).replace("\\","/"))})
    rows.sort(key=lambda x:(x["severity"]!="critical",-x["bytes"],-x["lines"],x["repo"],x["path"]))
    result={"schema":"source-surface-audit/v1","critical_thresholds":{"bytes":a.critical_bytes,"lines":a.critical_lines},"attention_thresholds":{"bytes":a.attention_bytes,"lines":a.attention_lines},"rows":rows,"critical_code_count":sum(x["severity"]=="critical" and not x["generated_or_historical"] for x in rows),"attention_code_count":sum(x["severity"]=="attention" and not x["generated_or_historical"] for x in rows)}
    a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8"); print(json.dumps({k:result[k] for k in ("schema","critical_code_count","attention_code_count")},indent=2)); return 0
if __name__=="__main__": raise SystemExit(main())