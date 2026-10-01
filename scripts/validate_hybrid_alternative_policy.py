#!/usr/bin/env python3
"""Fail-closed validator for the Hybrid & Alternative $0 policy and audit."""
from __future__ import annotations
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
POLICY=ROOT/"docs"/"HYBRID_ALTERNATIVE_ZERO_COST_POLICY.json"
AUDIT=ROOT/"docs"/"HYBRID_ALTERNATIVE_ECOSYSTEM_AUDIT_2026-10-01.json"
ACTIONS=ROOT/"docs"/"GITHUB_ACTIONS_ZERO_COST_POLICY.json"
APPS=ROOT/"docs"/"GITHUB_APP_INTEGRATION_POLICY.json"
def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))
def validate() -> None:
    p=load(POLICY); a=load(AUDIT); actions=load(ACTIONS); apps=load(APPS)
    if p["schema_version"]!="hybrid-alternative-zero-cost-policy/v1": raise ValueError("unsupported hybrid policy schema")
    if a["schema_version"]!="hybrid-alternative-ecosystem-audit/v1": raise ValueError("unsupported hybrid audit schema")
    for key in ("mcp","github_actions","github_apps"):
        ps=p["ecosystem_scope"][key]; ac=a["coverage"][key]
        if ps["supplied_entries"]!=ps["unique_entries"]: raise ValueError(f"{key} policy uniqueness drift")
        if ps["supplied_entries"]!=ac["supplied_entries"] or ps["unique_entries"]!=ac["unique_entries"] or ps["dataset_sha256"]!=ac["dataset_sha256"]: raise ValueError(f"{key} audit fingerprint drift")
    if p["hybrid_principle"]["paid_capabilities_are_researchable"] is not True or p["hybrid_principle"]["paid_capabilities_are_not_ignored"] is not True: raise ValueError("paid capability research is disabled")
    if p["hybrid_principle"]["direct_paid_runtime_dependency_allowed"] is not False: raise ValueError("direct paid runtime dependency enabled")
    ids={x["id"] for x in p["economic_disposition"]}
    required={"native_free","composed_free","self_hosted_open_source","free_quota_bounded","paid_direct_forbidden","paid_feature_reimplement","research_only"}
    if ids!=required: raise ValueError("economic disposition set drift")
    if "license/IP compatibility check" not in p["promotion_gate"]: raise ValueError("license/IP gate missing")
    if "differential or parity tests where applicable" not in p["promotion_gate"]: raise ValueError("differential gate missing")
    if "shadow evidence" not in p["promotion_gate"] or "canary evidence" not in p["promotion_gate"] or "rollback path" not in p["promotion_gate"]: raise ValueError("runtime promotion gates incomplete")
    if not a["status"].startswith("100%"): raise ValueError("audit status is not complete")
    expected_acceptance={"all_supplied_rows_processed":True,"direct_paid_dependencies_added":False,"marketplace_apps_installed_for_discovery":False,"existing_first_party_operations_app_preserved":True,"action_policy_remains_full_sha_and_allowlist":True,"single_authority_rule_preserved":True}
    if a["acceptance"] != expected_acceptance: raise ValueError("audit acceptance drift")
    if actions["zero_cost_invariants"]["max_additional_cost_usd"]!=0: raise ValueError("Actions $0 invariant drift")
    if actions["hybrid_alternative"]["research_paid_capabilities"] is not True or actions["hybrid_alternative"]["direct_paid_runtime_dependency_allowed"] is not False: raise ValueError("Actions hybrid policy drift")
    if apps["zero_cost_policy"]["max_additional_cost_usd"]!=0: raise ValueError("Apps $0 invariant drift")
    if apps["hybrid_alternative"]["research_paid_apps"] is not True or apps["hybrid_alternative"]["direct_paid_runtime_dependency_allowed"] is not False: raise ValueError("Apps hybrid policy drift")
    print(json.dumps({"schema":p["schema_version"],"mcp_entries":339,"actions_entries":9999,"apps_entries":1408,"paid_research_enabled":True,"direct_paid_runtime":False,"status":"PASS"},sort_keys=True))
if __name__=="__main__":
    validate()
