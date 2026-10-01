from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).parents[1]
WORKFLOW_ROOT = ROOT / ".github" / "workflows"
SHA_REF = re.compile(r"^[0-9a-f]{40}$")


def test_dependency_review_is_capability_aware_and_bounded() -> None:
    workflow = (WORKFLOW_ROOT / "dependency-review.yml").read_text(encoding="utf-8")
    assert "pull_request:" in workflow
    assert "workflow_dispatch:" in workflow
    assert "permissions:\n  contents: read" in workflow
    assert "timeout-minutes: 5" in workflow
    assert "timeout-minutes: 10" in workflow
    assert "concurrency:" in workflow
    assert "cancel-in-progress: true" in workflow
    assert "dependency-graph/sbom" in workflow
    assert "200)" in workflow
    assert "404)" in workflow
    assert "if: needs.dependency-graph-preflight.outputs.enabled == 'true'" in workflow
    assert "fail-on-severity: high" in workflow


def test_marketplace_derived_workflow_pins_all_actions_to_full_sha() -> None:
    workflow = (WORKFLOW_ROOT / "dependency-review.yml").read_text(encoding="utf-8")
    refs = re.findall(r"uses:\s*[^@\s]+@([^\s#]+)", workflow)
    assert refs
    assert all(SHA_REF.fullmatch(ref) for ref in refs)
    assert "3d3c42e5aac5ba805825da76410c181273ba90b1" in refs
    assert "a1d282b36b6f3519aa1f3fc636f609c47dddb294" in refs
