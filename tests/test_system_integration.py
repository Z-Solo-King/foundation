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