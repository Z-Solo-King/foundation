from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).parents[1]
WORKFLOW_ROOT = ROOT / ".github" / "workflows"
SHA_REF = re.compile(r"^[0-9a-f]{40}$")


def test_osv_scanner_workflow_is_bounded_and_advisory() -> None:
    workflow = (WORKFLOW_ROOT / "osv-scanner.yml").read_text(encoding="utf-8")
    assert "pull_request:" in workflow
    assert "schedule:" in workflow
    assert "workflow_dispatch:" in workflow
    assert "permissions:\n  contents: read" in workflow
    assert "security-events: write" in workflow
    assert "timeout-minutes: 15" in workflow
    assert "concurrency:" in workflow
    assert "cancel-in-progress: true" in workflow
    assert "continue-on-error: true" in workflow
    assert "--recursive" in workflow


def test_marketplace_derived_workflow_pins_actions_to_full_sha() -> None:
    workflow = (WORKFLOW_ROOT / "osv-scanner.yml").read_text(encoding="utf-8")
    refs = re.findall(r"uses:\s*[^@\s]+@([^\s#]+)", workflow)
    assert refs
    assert all(SHA_REF.fullmatch(ref) for ref in refs)
    assert "a345acffa64b0eaede81a3d9aae6141214d9c8fc" in refs
