from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_extractor_governance_bridge_has_one_trusted_trigger_class():
    workflow = (ROOT / ".github/workflows/extractor-surface-governance.yml").read_text(encoding="utf-8")
    assert "push:" in workflow
    assert "branches: [main]" in workflow
    assert "schedule:" in workflow
    assert "workflow_dispatch:" in workflow
    assert "pull_request:" not in workflow
    assert "pull_request_target:" not in workflow
    assert "merge_group:" not in workflow
    assert "permissions:" in workflow
    assert "contents: read" in workflow


def test_extractor_governance_bridge_registers_with_workflow_authority():
    registry = json.loads(
        (ROOT / "docs/WORKFLOW_AUTHORITY_REGISTRY.json").read_text(encoding="utf-8")
    )
    privileged = {entry[0]: entry[1] for entry in registry["explicit_privileged_workflows"]}
    assert privileged[".github/workflows/extractor-surface-governance.yml"] == "private_audit"


def test_extractor_governance_bridge_invokes_canonical_operations_audits():
    workflow = (ROOT / ".github/workflows/extractor-surface-governance.yml").read_text(encoding="utf-8")
    assert "operations/tools/oldest_surface_audit.py" in workflow
    assert "operations/tools/extractor_surface_audit.py" in workflow
    assert "operations/tools/feature_surface_audit.py" in workflow
    assert "operations/extractor_mapper/execution_plan.py" in workflow
    assert "operations/extractor_mapper/policies/retention.py" in workflow
    assert "test ! -e operations/extractor_mapper/execution_plan.py" in workflow
    assert "test ! -e operations/extractor_mapper/policies/retention.py" in workflow
