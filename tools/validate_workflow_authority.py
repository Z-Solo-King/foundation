#!/usr/bin/env python3
"""Fail-closed workflow authority and public/private boundary validator."""
from __future__ import annotations
import json
import re
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
REGISTRY=ROOT/"docs"/"WORKFLOW_AUTHORITY_REGISTRY.json"
WORKFLOWS=ROOT/".github"/"workflows"
WORKFLOW_EVENTS=frozenset({
    "pull_request",
    "pull_request_target",
    "push",
    "schedule",
    "workflow_dispatch",
    "merge_group",
    "workflow_run",
})

def _events(text:str)->set[str]:
    found=set()
    for line in text.splitlines():
        stripped=line.lstrip()
        if not stripped or stripped.startswith("#"):
            continue
        event, separator, _ = stripped.partition(":")
        if separator and not event.startswith("-") and event.strip() in WORKFLOW_EVENTS:
            found.add(event.strip())
    return found

def _push_branches(text:str)->list[str]:
    lines=text.splitlines()
    for index,line in enumerate(lines):
        if line.strip() != "push:":
            continue
        push_indent=len(line)-len(line.lstrip())
        block=[]
        for child in lines[index+1:]:
            if not child.strip():
                block.append(child)
                continue
            indent=len(child)-len(child.lstrip())
            if indent <= push_indent:
                break
            block.append(child)
        block_text="\n".join(block)
        inline=re.search(r"(?m)^\s*branches:\s*\[([^\]]+)\]",block_text)
        if inline:
            return [value.strip().strip("'\\\"") for value in inline.group(1).split(",") if value.strip()]
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
        is_priv=any(marker in text for marker in markers)
        if is_priv and rel not in privileged:
            errors.append(f"{rel}: privileged workflow is not explicitly registered")
        if rel in feed and any(marker in text for marker in markers):
            errors.append(f"{rel}: public feed workflow contains a privileged marker")
        if is_priv and events & forbidden:
            errors.append(f"{rel}: privileged workflow has forbidden untrusted trigger: {sorted(events & forbidden)}")
        branches=_push_branches(text)
        if is_priv and "push" in events and branches != [reg["policy"]["privileged_push_branch"]]:
            errors.append(f"{rel}: privileged push must be main-only")
        if is_priv and "workflow_run" in events:
            expected_sources=reg["policy"].get("trusted_workflow_run_sources",{}).get(rel)
            if not expected_sources:
                errors.append(f"{rel}: privileged workflow_run requires explicit trusted upstream registration")
            elif _workflow_run_sources(text) != sorted(set(expected_sources)):
                errors.append(f"{rel}: workflow_run source mismatch")
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
            errors.append(f"{rel}: workflow_run source mismatch")
    return sorted(set(errors))

if __name__=="__main__":
    errors=validate()
    if errors:
        print(f"workflow authority policy: FAIL ({len(errors)} policy violations)")
        raise SystemExit(1)
    print(f"workflow authority policy: PASS ({len(workflow_paths())} workflows scanned)")
