"""Validation helpers for the project-native AI/agent benchmark manifest."""
from __future__ import annotations
from collections import Counter
from typing import Any, Mapping

def validate_manifest(payload: Mapping[str, Any]) -> list[str]:
    errors=[]
    if payload.get("schema")!="ai-agent-benchmark-task-matrix/v1": errors.append("unexpected schema")
    tasks=payload.get("tasks"); lanes=payload.get("lanes"); weights=payload.get("scoring_dimensions")
    if not isinstance(tasks,list) or not tasks: return errors+["tasks must be a non-empty list"]
    if not isinstance(lanes,list) or len(lanes)!=6: errors.append("exactly six benchmark lanes are required")
    if not isinstance(weights,list) or not weights: errors.append("scoring_dimensions must be non-empty")
    else:
        total=sum(float(x.get("weight",0)) for x in weights if isinstance(x,Mapping))
        if abs(total-1.0)>1e-9: errors.append(f"scoring weights must sum to 1.0, got {total}")
    ids=[t.get("task_id") for t in tasks if isinstance(t,Mapping)]
    for task_id,count in Counter(ids).items():
        if count!=1: errors.append(f"duplicate task_id: {task_id}")
    if len(tasks)!=24: errors.append(f"expected 24 tasks, got {len(tasks)}")
    lane_codes={x.get("code") for x in lanes if isinstance(x,Mapping)}
    for task in tasks:
        if not isinstance(task,Mapping): errors.append("task entry is not an object"); continue
        if task.get("lane") not in lane_codes: errors.append(f"unknown lane for {task.get('task_id')}")
        if task.get("repeat_count")!=3: errors.append(f"repeat_count must be 3 for {task.get('task_id')}")
        required=set(task.get("required_checks",[]))
        for check in ("canonical_owner","exact_revision","evidence_ladder","no_unsupported_completion_claim"):
            if check not in required: errors.append(f"missing required check {check} for {task.get('task_id')}")
    return errors
