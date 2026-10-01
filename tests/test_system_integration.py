from __future__ import annotations
import json, subprocess, sys
from pathlib import Path
ROOT=Path(__file__).parents[1]
def test_integration_contract_is_versioned_and_complete():
    p=json.loads((ROOT/"docs/SYSTEM_INTEGRATION_CONTRACT.json").read_text())
    assert p["schema_version"]=="system-integration-contract/v1"
    assert len(p["canonical_flow"])>=10
    assert {"ai_automation","ai_api","audit","quality","learning","self_evolution","mapper_extractor","evidence"} <= set(p["cross_cutting_controls"])
    assert p["architecture"]["one_authority_per_responsibility"] is True
def test_project_matrix_binds_to_cross_cutting_contract():
    m=json.loads((ROOT/"docs/PROJECT_IMPROVEMENT_MATRIX.json").read_text())
    assert m["system_integration_contract"]=="docs/SYSTEM_INTEGRATION_CONTRACT.json"
    assert len(m["cross_cutting_controls"])>=8
def test_integration_validator_passes_against_live_checkouts():
    ops=ROOT.parent/"operations"
    if not ops.exists(): return
    subprocess.check_call([sys.executable,str(ROOT/"tools/validate_system_integration.py"),"--foundation-root",str(ROOT),"--operations-root",str(ops),"--strict"])

def test_production_pin_manifest_is_consistent():
    manifest = json.loads((ROOT/"docs/OPERATIONS_PIN_MANIFEST.json").read_text())
    approval = json.loads((ROOT/"docs/OPERATIONS_MAIN_APPROVAL.json").read_text())
    sync = json.loads((ROOT/"docs/FAMILY_SYNC_STATE.json").read_text())
    canonical = manifest["pins"]["production_runtime"]["sha"]
    assert len(canonical) == 40
    assert approval["approved_sha"] == canonical
    assert approval["production_observed_sha"] != canonical
    assert approval["observed_state"] == "PENDING_PRODUCTION_CERTIFICATION"
    assert approval["promotion_evidence"]["production_certification_required_after_pin_change"] is True
    assert sync["runtime_pins"]["production_operations"] == canonical
