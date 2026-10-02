#!/usr/bin/env python3
"""Deterministic cross-family equivalence and CrossFire coverage audit."""
from __future__ import annotations
import argparse, ast, hashlib, json, re, subprocess
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

SCHEMA="cross-system-equivalence/v1"
SKIP={".git","__pycache__",".pytest_cache",".mypy_cache",".ruff_cache",".tox",".nox",
      "node_modules",".venv","venv","dist","build","target"}
PAT={
 ".py":re.compile(r"^\s*(?:async\s+def|def)\s+([A-Za-z_]\w*)\s*\(",re.M),
 ".rs":re.compile(r"^\s*(?:pub\s+)?(?:async\s+)?fn\s+([A-Za-z_]\w*)\s*[\(<]",re.M),
 ".go":re.compile(r"^\s*func\s+(?:\([^)]*\)\s*)?([A-Za-z_]\w*)\s*\(",re.M),
 ".ts":re.compile(r"^\s*(?:export\s+)?(?:async\s+)?function\s+([A-Za-z_]\w*)\s*\(",re.M),
 ".tsx":re.compile(r"^\s*(?:export\s+)?(?:async\s+)?function\s+([A-Za-z_]\w*)\s*\(",re.M),
 ".js":re.compile(r"^\s*(?:export\s+)?(?:async\s+)?function\s+([A-Za-z_]\w*)\s*\(",re.M),
 ".jsx":re.compile(r"^\s*(?:export\s+)?(?:async\s+)?function\s+([A-Za-z_]\w*)\s*\(",re.M),
 ".mjs":re.compile(r"^\s*(?:export\s+)?(?:async\s+)?function\s+([A-Za-z_]\w*)\s*\(",re.M),
 ".kt":re.compile(r"^\s*(?:public\s+|private\s+|internal\s+|protected\s+|suspend\s+)*fun\s+([A-Za-z_]\w*)\s*\(",re.M),
 ".swift":re.compile(r"^\s*(?:public\s+|private\s+|internal\s+|fileprivate\s+|mutating\s+|static\s+)*func\s+([A-Za-z_]\w*)\s*\(",re.M),
 ".nim":re.compile(r"^\s*(?:proc|func|method|iterator|template)\s+([A-Za-z_]\w*)\b",re.M),
 ".zig":re.compile(r"^\s*pub\s+fn\s+([A-Za-z_]\w*)\s*\(",re.M),
 ".gleam":re.compile(r"^\s*(?:pub\s+)?fn\s+([A-Za-z_]\w*)\s*\(",re.M),
 ".php":re.compile(r"^\s*(?:public|protected|private|static|\s)*function\s+([A-Za-z_]\w*)\s*\(",re.M),
}
TOK=re.compile(r"[A-Za-z0-9_]+")

def now(): return datetime.now(timezone.utc).isoformat()

def tracked(root):
    try:
        raw=subprocess.check_output(["git","-C",str(root),"ls-files","-z"],timeout=30)
        vals=raw.decode("utf-8","surrogateescape").split("\0")
    except Exception:
        vals=[p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file()]
    return sorted({v for v in vals if v and not any(x in SKIP for x in Path(v).parts)})

def sha(path):
    h=hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""): h.update(chunk)
    return h.hexdigest()

def decls(path):
    text=path.read_text(encoding="utf-8",errors="ignore")
    if path.suffix.lower()==".py":
        try:
            tree=ast.parse(text)
            return sorted({n.name for n in ast.walk(tree) if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))})
        except SyntaxError: pass
    p=PAT.get(path.suffix.lower())
    return sorted(set(p.findall(text))) if p else []

def inventory(root):
    files=tracked(root); out=[]; names=[]
    for rel in files:
        p=root/rel
        if not p.is_file(): continue
        try: d=decls(p); s=sha(p); n=p.stat().st_size
        except OSError: continue
        out.append({"path":rel,"sha256":s,"bytes":n,"extension":p.suffix.lower(),"declarations":d})
        names.extend({"path":rel,"name":x,"language":p.suffix.lower().lstrip(".")} for x in d)
    return {"files":out,"tracked_file_count":len(files),
            "extension_counts":dict(sorted(Counter((Path(x).suffix.lower().lstrip(".") or "[none]") for x in files).items())),
            "declarations":names}

def load_map(root):
    p=root/"docs/AI_PROJECT_MAP.json"
    if not p.is_file(): raise ValueError(f"missing {p}")
    d=json.loads(p.read_text(encoding="utf-8"))
    if d.get("schema_version")!="ai-project-map/v2": raise ValueError(f"bad map schema in {p}")
    return d

def tok(v): return {x.casefold() for x in TOK.findall(str(v or "")) if len(x)>1}
def jac(a,b):
    x,y=tok(a),tok(b)
    return round(len(x&y)/len(x|y),4) if x and y else 0.0

def pair_policies(f,o):
    fp,op=f.get("policy_catalog",{}),o.get("policy_catalog",{})
    ids=sorted(set(fp)|set(op)); rows=[]
    for i in ids:
        a,b=fp.get(i),op.get(i)
        if a is None: state="operations_only_scope"
        elif b is None: state="foundation_only_scope"
        elif a==b: state="exact"
        else: state="divergent"
        rows.append({"id":i,"foundation":a,"operations":b,"state":state})
    return {"foundation_count":len(fp),"operations_count":len(op),"pair_count":len(rows),
            "rows":rows,"divergent":[r for r in rows if r["state"]=="divergent"]}

def feature_score(a,b):
    vals=[jac(a.get(k),b.get(k)) for k in ("id","usage","key","surfaces","policy_logic","policies")]
    return round(sum(vals)/len(vals),4)

def pair_features(f,o):
    left,right=f.get("feature_domains",[]),o.get("feature_domains",[])
    overlaps=[]
    for a in left:
        for b in right:
            s=feature_score(a,b)
            if s>=0.20:
                overlaps.append({"foundation":a.get("id"),"operations":b.get("id"),
                                 "similarity":s,
                                 "shared_policies":sorted(set(a.get("policies",[]))&set(b.get("policies",[])))})
    matched_f={x["foundation"] for x in overlaps}; matched_o={x["operations"] for x in overlaps}
    return {"foundation_count":len(left),"operations_count":len(right),"cartesian_pairs":len(left)*len(right),
            "overlaps":sorted(overlaps,key=lambda x:(-x["similarity"],x["foundation"],x["operations"])),
            "unpaired_foundation":[x.get("id") for x in left if x.get("id") not in matched_f],
            "unpaired_operations":[x.get("id") for x in right if x.get("id") not in matched_o]}

def pair_declarations(fi,oi):
    l,r=defaultdict(list),defaultdict(list)
    for x in fi["declarations"]: l[x["name"].casefold()].append(x)
    for x in oi["declarations"]: r[x["name"].casefold()].append(x)
    rows=[]
    for name in sorted(set(l)&set(r)):
        for a in l[name]:
            for b in r[name]:
                rows.append({"name":name,"foundation":a["path"],"operations":b["path"],"state":"same_name"})
    return {"foundation_count":len(fi["declarations"]),"operations_count":len(oi["declarations"]),
            "cartesian_pairs":len(fi["declarations"])*len(oi["declarations"]),
            "same_name_pairs":rows,"shared_names":sorted(set(l)&set(r))}

def pair_files(fi,oi):
    l={x["sha256"]:x["path"] for x in fi["files"]}; r={x["sha256"]:x["path"] for x in oi["files"]}
    same=[{"sha256":k,"foundation":l[k],"operations":r[k]} for k in sorted(set(l)&set(r))]
    return {"cartesian_pairs":len(fi["files"])*len(oi["files"]),"exact_same_content":same}

def architecture(f,o):
    out={}
    for k in ("node_types","edge_types"):
        a=set(f.get("connection_model",{}).get(k,[])); b=set(o.get("connection_model",{}).get(k,[]))
        out[k]={"shared":sorted(a&b),"foundation_only":sorted(a-b),"operations_only":sorted(b-a)}
    a=f.get("combined_architecture",{}).get("flow",[]); b=o.get("combined_architecture",{}).get("flow",[])
    out["flows"]={"shared":sorted(set(a)&set(b)),"foundation_only":sorted(set(a)-set(b)),
                  "operations_only":sorted(set(b)-set(a))}
    return out

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--foundation-root",type=Path,required=True)
    ap.add_argument("--operations-root",type=Path,required=True)
    ap.add_argument("--output",type=Path,required=True)
    ap.add_argument("--strict",action="store_true")
    a=ap.parse_args()
    fi,oi=inventory(a.foundation_root),inventory(a.operations_root)
    fm,om=load_map(a.foundation_root),load_map(a.operations_root)
    policies,features=pair_policies(fm,om),pair_features(fm,om)
    functions,files=pair_declarations(fi,oi),pair_files(fi,oi)
    arch=architecture(fm,om)
    counts={"foundation":{"files":fi["tracked_file_count"],"functions":fm.get("function_metrics",{}).get("canonical_surface_declarations",len(fi["declarations"])),"features":len(fm.get("feature_domains",[])),"policies":len(fm.get("policy_catalog",{}))},
            "operations":{"files":oi["tracked_file_count"],"functions":om.get("function_metrics",{}).get("canonical_surface_declarations",len(oi["declarations"])),"features":len(om.get("feature_domains",[])),"policies":len(om.get("policy_catalog",{}))}}
    findings=[]
    if policies["divergent"]: findings.append({"severity":"high","kind":"shared_policy_divergence","items":policies["divergent"]})
    if features["unpaired_foundation"] or features["unpaired_operations"]:
        findings.append({"severity":"info","kind":"scope_or_nonoverlap_features","foundation":features["unpaired_foundation"],"operations":features["unpaired_operations"]})
    if files["exact_same_content"]:
        findings.append({"severity":"info","kind":"exact_duplicate_content","items":files["exact_same_content"][:200]})
    stale=[]
    for repo,m in (("foundation",fm),("operations",om)):
        head=m.get("source_head_at_generation")
        if not re.fullmatch(r"[0-9a-f]{40}",str(head or "")): stale.append(repo)
    receipt={
      "schema_version":SCHEMA,"generated_at":now(),"counts":counts,
      "formula":{"expression":"N^2 x N^2 = N^4","interpretation":"typed Cartesian comparisons are materialized; the symbolic N^4 expansion is retained as the audit model"},
      "pairwise":{"policies":policies,"features":features,"functions":functions,"files":files,"architecture":arch},
      "coverage":{"foundation_tracked_files":fi["tracked_file_count"],"operations_tracked_files":oi["tracked_file_count"],
                  "foundation_inventory_records":len(fi["files"]),"operations_inventory_records":len(oi["files"]),
                  "languages_seen":sorted({x["language"] for x in fi["declarations"]+oi["declarations"]}),
                  "map_snapshot_stale_unknown":stale},
      "findings":findings,
      "strict_pass":not policies["divergent"] and len(fi["files"])==fi["tracked_file_count"] and len(oi["files"])==oi["tracked_file_count"],
      "limitations":["Lexical/name similarity is not semantic equivalence proof.","Runtime bindings/deployments require fresh live receipts.","Scope-only policies/features are not defects by themselves.","AI/provider results remain supporting evidence, never policy authority."]
    }
    a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps({"schema_version":SCHEMA,"strict_pass":receipt["strict_pass"],"counts":counts,
                      "policy_pairs":policies["pair_count"],"feature_pairs":features["cartesian_pairs"],
                      "function_pairs":functions["cartesian_pairs"],"file_pairs":files["cartesian_pairs"],
                      "shared_function_names":len(functions["shared_names"]),"exact_duplicate_files":len(files["exact_same_content"]),
                      "findings":len(findings)},indent=2))
    return 0 if receipt["strict_pass"] or not a.strict else 1

if __name__=="__main__": raise SystemExit(main())
