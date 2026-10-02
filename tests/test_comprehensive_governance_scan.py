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
        "migration_candidate_missing_evidence",
        "canonical_policy_surface_missing",
        "canonical_runtime_surface_missing",
        "attention_source_size",
    ):
        assert needle in source

def test_publisher_has_stable_deduplication_markers():
    source = (ROOT / "tools/publish_governance_findings.py").read_text(encoding="utf-8")
    assert "governance-finding:" in source
    assert "governance-digest:" in source


def test_scanner_declares_adaptive_crossfire_policy():
    source = (ROOT / "tools/comprehensive_governance_scan.py").read_text(encoding="utf-8")
    assert "CROSSFIRE_PROVIDER_TARGET=6" in source
    assert "CROSSFIRE_STRONG_THRESHOLD=5" in source
    assert "def crossfire_policy" in source
    assert '"ai_escalation_required"' in source


def test_governance_sweep_uses_existing_provider_crossfire_without_duplicate_dispatch():
    workflow = (ROOT / ".github/workflows/twice-daily-governance-sweep.yml").read_text(encoding="utf-8")
    assert "Cross-fire AI escalation decision" in workflow
    assert "live-ai-provider-crossfire.yml" in workflow
    assert "already queued/running" in workflow
    assert "DRY_RUN" in workflow
