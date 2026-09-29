#!/usr/bin/env python3
"""Fail-closed workflow authority and public/private boundary validator."""
from __future__ import annotations
import json
import re
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
REGISTRY=ROOT/"docs"/"WORKFLOW_AUTHORITY_REGISTRY.json"
WORKFLOWS=ROOT/".github"/"workflows"

def _events(text:str)->set[str]:
    return {
        name for name in ("pull_request","pull_request_target","push","schedule","workflow_dispatch")
        if re.search(rf"(?m)^\s{{0,2}}{name}\s*:", text)
    }

def _push_branches(text:str)->list[str]:
    head=text.split("jobs:",1)[0]
    m=re.search(r"(?ms)^\s{2}push:\s*\n(.*?)(?=^\s{2}[A-Za-z0-9_.-]+:|^jobs:)",head)
    if not m:
        return []
    block=m.group(1)
    inline=re.search(r"(?m)^\s{4}branches:\s*\[([^\]]+)\]",block)
    if inline:
        return [v.strip().strip("'\\\"") for v in inline.group(1).split(",") if v.strip()]
    bm=re.search(r"(?ms)^\s{4}branches:\s*\n(.*?)(?=^\s{4}[A-Za-z0-9_.-]+:|\Z)",block)
    if not bm:
        return []
    return re.findall(r"(?m)^\s{6}-\s*['\\\"]?([^'\\\"\s]+)",bm.group(1))

def workflow_paths():
    return sorted(WORKFLOWS.glob("*.yml"))+sorted(WORKFLOWS.glob("*.yaml"))

def validate()->list[str]:
    reg=json.loads(REGISTRY.read_text(encoding="utf-8"))
    privileged=dict(reg.get("explicit_privileged_workflows",[]))
    feed=set(reg.get("public_feed_workflows",{}))
    markers=reg["policy"]["privileged_markers"]
    forbidden=set(reg["policy"]["forbidden_events"])
    errors=[]
    seen=set()
    for path in workflow_paths():
        rel=str(path.relative_to(ROOT)).replace("\\","/")
        seen.add(rel)
        text=path.read_text(encoding="utf-8")
        events=_events(text)
        is_priv=any(m in text for m in markers)
        if is_priv and rel not in privileged:
            errors.append(f"{rel}: privileged workflow is not explicitly registered")
        if rel in feed and any(m in text for m in markers):
            errors.append(f"{rel}: public feed workflow contains a privileged marker")
        if is_priv and events & forbidden:
            errors.append(f"{rel}: privileged workflow has forbidden PR trigger: {sorted(events & forbidden)}")
        branches=_push_branches(text)
        if is_priv and "push" in events and branches and branches != [reg["policy"]["privileged_push_branch"]]:
            errors.append(f"{rel}: privileged push must be main-only, found {branches}")
        if rel==".github/workflows/sync-secrets.yml":
            if "environment: production-secret-sync" not in text:
                errors.append(f"{rel}: missing protected environment")
            if "github.ref == 'refs/heads/main'" not in text:
                errors.append(f"{rel}: missing main guard")
    for rel in feed:
        if rel not in seen:
            errors.append(f"{rel}: registry references missing workflow")
    return sorted(set(errors))

if __name__=="__main__":
    errors=validate()
    if errors:
        for e in errors: print("ERROR:",e)
        raise SystemExit(1)
    print(f"workflow authority policy: PASS ({len(workflow_paths())} workflows scanned)")
