#!/usr/bin/env python3
"""Fail-closed cross-repository cohesion validator."""
from __future__ import annotations
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
CONTRACT=ROOT/"docs/SYSTEM_INTEGRATION_CONTRACT.json"
MATRIX=ROOT/"docs/PROJECT_IMPROVEMENT_MATRIX.json"

def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))

def require_text(path: Path, needles: list[str], errors: list[str], label: str) -> None:
    if not path.is_file():
        errors.append(f"{label}:missing")
        return
    text=path.read_text(encoding="utf-8",errors="ignore")
    for needle in needles:
        if needle not in text: errors.append(f"{label}:missing-anchor:{needle}")

def main() -> int:
    import argparse
    p=argparse.ArgumentParser(); p.add_argument("--foundation-root",type=Path,required=True); p.add_argument("--operations-root",type=Path); p.add_argument("--strict",action="store_true")
    args=p.parse_args(); errors=[]
    contract=load(args.foundation_root/"docs/SYSTEM_INTEGRATION_CONTRACT.json")
    matrix=load(args.foundation_root/"docs/PROJECT_IMPROVEMENT_MATRIX.json")
    if contract.get("schema_version")!="system-integration-contract/v1": errors.append("contract schema mismatch")
    if matrix.get("system_integration_contract")!="docs/SYSTEM_INTEGRATION_CONTRACT.json": errors.append("project matrix not bound to integration contract")
    controls=matrix.get("cross_cutting_controls",{})
    required_controls=set(contract.get("cross_cutting_controls",{}))
    if set(controls)!=required_controls: errors.append("cross-cutting control set drift")
    for stage in contract.get("canonical_flow",[]):
        for key in ("stage","owner","output"):
            if not stage.get(key): errors.append(f"flow stage missing {key}")
    f=args.foundation_root; o=args.operations_root
    for rel in contract["required_cross_repo_anchors"]["foundation"]: require_text(f/rel, [], errors, f"foundation:{rel}")
    if o is None:
        o=None
    if o is not None:
        for rel in contract["required_cross_repo_anchors"]["operations"]:
        pth=o/rel
        if rel.endswith("/"):
            if not pth.is_dir(): errors.append(f"operations:{rel}:missing")
        else: require_text(pth, [], errors, f"operations:{rel}")
    require_text(f/"tools/autonomous_mission_router.mjs",["PROJECT_IMPROVEMENT_MATRIX","scheduling_only"],errors,"foundation:router")
    require_text(f/"tools/autonomous_engineering_supervisor.mjs",["validatePlan","PROJECT_IMPROVEMENT_MATRIX","component_improvement"],errors,"foundation:supervisor")
    if o is not None:\n        require_text(o/"private/evolution_engine.py",["private.evolution_score","next_learning_action"],errors,"operations:evolution-engine")
        require_text(o/"private/chatbot/chat_learning.py",["LearningAuthority.CANDIDATE","ChatLearningObservation"],errors,"operations:chat-learning")
        require_text(o/"private/chatbot/feedback_evaluation_bridge.py",["EvaluationCaseCandidate","LearningAuthority.CANDIDATE"],errors,"operations:feedback-bridge")
        require_text(o/"private/strategy_matrix.py",["CandidateDisposition","ELIGIBLE_FOR_SHADOW"],errors,"operations:strategy")
        require_text(o/"private/self_evolution_boundary.py",["ProtectedAuthority","CandidateStage.CANARY"],errors,"operations:self-evolution")
        require_text(o/"extractor_mapper/extraction/generic.py",["class"],errors,"operations:extractor")
    if not (o/".github/workflows").exists(): pass
    else:
        ymls=list((o/".github/workflows").glob("*"))
        if ymls: errors.append("operations:hosted workflow authority must remain absent")
    status="PASS" if not errors else "FAIL"
    print(json.dumps({"schema":"system-integration-receipt/v1","status":status,"error_count":len(errors),"errors":errors},indent=2))
    return 0 if not errors else 1
if __name__=="__main__": raise SystemExit(main())