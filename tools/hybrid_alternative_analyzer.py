#!/usr/bin/env python3
"""Deterministic disposition engine for paid/external capability research."""
from __future__ import annotations
import argparse, json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
POLICY = ROOT / "docs" / "HYBRID_ALTERNATIVE_ZERO_COST_POLICY.json"

def _policy() -> dict:
    return json.loads(POLICY.read_text(encoding="utf-8"))

def classify(candidate: dict) -> dict:
    required={"ecosystem","source_id","capability","economic_class"}
    missing=sorted(required-set(candidate))
    if missing: raise ValueError(f"missing candidate fields: {missing}")
    p=_policy()
    classes={x["id"]:x for x in p["economic_disposition"]}
    kind=str(candidate["economic_class"])
    if kind not in classes: raise ValueError(f"unknown economic_class: {kind}")
    row=dict(candidate)
    if kind=="paid_direct_forbidden":
        row["direct_runtime_allowed"]=False
        row["recommended_route"]="analyze_public_behavior_then_reimplement_or_compose_free_capabilities"
    elif kind=="paid_feature_reimplement":
        row["direct_runtime_allowed"]=True
        row["recommended_route"]="native_or_open_source_reimplementation_after_differential_validation"
    else:
        row["direct_runtime_allowed"]=bool(classes[kind]["runtime_allowed"])
        row["recommended_route"]="use_existing_governed_route" if row["direct_runtime_allowed"] else "research_only_until_free_path_is_proven"
    row["required_gate"]=p["promotion_gate"]
    return row

def main() -> int:
    parser=argparse.ArgumentParser()
    parser.add_argument("--candidate-json", required=True)
    args=parser.parse_args()
    candidate=json.loads(args.candidate_json)
    if not isinstance(candidate,dict): raise ValueError("candidate must be an object")
    print(json.dumps(classify(candidate),indent=2,sort_keys=True))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
