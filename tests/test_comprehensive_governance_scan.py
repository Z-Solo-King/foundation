import json
from pathlib import Path

ROOT = Path(__file__).parents[1]

def test_governance_contract_declares_eight_lanes():
    payload = json.loads((ROOT / "docs/AUTONOMOUS_GOVERNANCE_SCAN_CONTRACT.json").read_text(encoding="utf-8"))
    assert payload["schema"] == "autonomous-governance-scan/v1"
    assert len(payload["lanes"]) == 8
    assert payload["cross_product"]["n2xn2"].startswith("Use bounded")

def test_scanner_contains_requested_control_surfaces():
    source = (ROOT / "tools/comprehensive_governance_scan.py").read_text(encoding="utf-8")
    for needle in (
        "exact_duplicate_content",
        "cross_repo_duplicate_content",
        "private_tree_in_public_repo",
        "migration_gate_incomplete",
        "critical_source_size",
        "task_family_parity",
        "quality_hard_gate_incomplete",
        "bounded_feature_policy_cross_product",
        "unregistered_privileged_workflow",
        "slow_workflow_runs",
    ):
        assert needle in source

def test_publisher_has_stable_deduplication_markers():
    source = (ROOT / "tools/publish_governance_findings.py").read_text(encoding="utf-8")
    assert "governance-finding:" in source
    assert "governance-digest:" in source
