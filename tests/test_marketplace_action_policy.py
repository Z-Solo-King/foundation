from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).parents[1]
WORKFLOW_ROOT = ROOT / ".github" / "workflows"
SHA_REF = re.compile(r"^[0-9a-f]{40}$")

def test_dependency_review_workflow_is_bounded_and_read_only() -> None:
    workflow = (WORKFLOW_ROOT / "dependency-review.yml").read_text(encoding="utf-8")
    assert "pull_request:" in workflow
    assert "workflow_dispatch:" in workflow
    assert "permissions:\n  contents: read" in workflow
    assert "timeout-minutes: 10" in workflow
    assert "concurrency:" in workflow
    assert "cancel-in-progress: true" in workflow
    assert "fail-on-severity: high" in workflow

def test_marketplace_derived_workflow_pins_action_to_full_sha() -> None:
    workflow = (WORKFLOW_ROOT / "dependency-review.yml").read_text(encoding="utf-8")
    match = re.search(r"uses:\s*actions/dependency-review-action@([^\s#]+)", workflow)
    assert match is not None
    assert SHA_REF.fullmatch(match.group(1))
    assert match.group(1) == "a1d282b36b6f3519aa1f3fc636f609c47dddb294"
