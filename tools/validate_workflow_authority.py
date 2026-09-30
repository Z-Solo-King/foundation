#!/usr/bin/env python3
"""Fail-closed workflow authority and public/private boundary validator."""
from __future__ import annotations
import json
import re
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
REGISTRY=ROOT/"docs"/"WORKFLOW_AUTHORITY_REGISTRY.json"
WORKFLOWS=ROOT/".github"/"workflows"
_EVENT_RE = re.compile(
    r"(?m)^\s{0,2}(pull_request|pull_request_target|push|schedule|workflow_dispatch|merge_group|workflow_run)\s*:"
)

def _events(text:str)->set[str]:
    return set(_EVENT_RE.findall(text))

def _push_branches(text:str)->list[str]:
    lines=text.splitlines()
    for index,line in enumerate(lines):
        if line.strip() != "push:":
            continue
        push_indent=len(line)-len(line.lstrip())
        block=[]
        for child in lines[index+1:]:
            stripped=child.strip()
            if not stripped:
                block.append(child)
                continue
            indent=len(child)-len(child.lstrip())
            if indent <= push_indent:
                break
            block.append(child)
        block_text="\n".join(block)
        inline=re.search(r"(?m)^\s*branches:\s*\[([^\]]+)\]",block_text)
        if inline:
            return [v.strip().strip("'\\\"") for v in inline.group(1).split(",") if v.strip()]
        listed=re.findall(r"(?m)^\s*-\s*['\\\"]?([^'\\\"\s]+)",block_text)
        return listed
    return []

def workflow_paths():
    return sorted(WORKFLOWS.glob("*.yml"))+sorted(WORKFLOWS.glob("*.yaml"))

def _workflow_run_sources(text:str)->list[str]:
    names=[]
    for block in re.findall(r"(?ms)workflows:\s*\[([^\]]+)\]",text):
        names.extend(re.findall(r"""['"]([^'"]+)['"]""",block))
    return sorted(set(names))

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
            errors.append(f"{rel}: privileged workflow has forbidden untrusted trigger: {sorted(events & forbidden)}")
        branches=_push_branches(text)
        if is_priv and "push" in events and branches != [reg["policy"]["privileged_push_branch"]]:
            errors.append(f"{rel}: privileged push must be main-only, found {branches or ['<unrestricted>']}")
        if is_priv and "workflow_run" in events:
            expected_sources=reg["policy"].get("trusted_workflow_run_sources", {}).get(rel)
            if not expected_sources:
                errors.append(f"{rel}: privileged workflow_run requires explicit trusted upstream registration")
            elif _workflow_run_sources(text) != sorted(set(expected_sources)):
                errors.append(f"{rel}: workflow_run source mismatch; declared={_workflow_run_sources(text)} expected={sorted(set(expected_sources))}")
        if rel==".github/workflows/sync-secrets.yml":
            if "environment: production-secret-sync" not in text:
                errors.append(f"{rel}: missing protected environment")
            if "github.ref == 'refs/heads/main'" not in text:
                errors.append(f"{rel}: missing main guard")
    for rel in feed:
        if rel not in seen:
            errors.append(f"{rel}: registry references missing workflow")
    for rel,sources in reg["policy"].get("trusted_workflow_run_sources",{}).items():
        path=ROOT/rel
        if not path.is_file():
            errors.append(f"{rel}: trusted workflow_run registry target is missing")
            continue
        text=path.read_text(encoding="utf-8")
        if "workflow_run:" not in text:
            errors.append(f"{rel}: trusted workflow_run registry entry exists but workflow_run is absent")
        elif _workflow_run_sources(text) != sorted(set(sources)):
            errors.append(f"{rel}: workflow_run source mismatch; declared={_workflow_run_sources(text)} expected={sorted(set(sources))}")
    return sorted(set(errors))

if __name__=="__main__":
    errors=validate()
    if errors:
        for e in errors:
            print("ERROR:",e)
        raise SystemExit(1)
    print(f"workflow authority policy: PASS ({len(workflow_paths())} workflows scanned)")
