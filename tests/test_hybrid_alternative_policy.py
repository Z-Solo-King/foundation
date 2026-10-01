from __future__ import annotations
import json, subprocess, sys
from pathlib import Path
ROOT=Path(__file__).parents[1]
POLICY=ROOT/"docs"/"HYBRID_ALTERNATIVE_ZERO_COST_POLICY.json"
ANALYZER=ROOT/"tools"/"hybrid_alternative_analyzer.py"

def test_all_supplied_ecosystems_are_covered() -> None:
    p=json.loads(POLICY.read_text(encoding="utf-8"))
    assert p["ecosystem_scope"]["mcp"]["supplied_entries"]==339
    assert p["ecosystem_scope"]["github_actions"]["supplied_entries"]==9999
    assert p["ecosystem_scope"]["github_apps"]["supplied_entries"]==1408
    assert all(x["supplied_entries"]==x["unique_entries"] for x in p["ecosystem_scope"].values())

def _run(candidate: dict) -> dict:
    out=subprocess.check_output([sys.executable,str(ANALYZER),"--candidate-json",json.dumps(candidate)],text=True)
    return json.loads(out)

def test_paid_feature_can_be_reimplemented() -> None:
    row=_run({"ecosystem":"github_app","source_id":"premium-review","capability":"ai-review","economic_class":"paid_feature_reimplement"})
    assert row["direct_runtime_allowed"] is True
    assert "reimplementation" in row["recommended_route"]

def test_paid_direct_runtime_is_denied() -> None:
    row=_run({"ecosystem":"mcp","source_id":"hosted-search","capability":"web-search","economic_class":"paid_direct_forbidden"})
    assert row["direct_runtime_allowed"] is False
    assert "reimplement" in row["recommended_route"]


def test_validator_passes() -> None:
    subprocess.check_output([sys.executable, str(ROOT / "scripts" / "validate_hybrid_alternative_policy.py")], text=True)
