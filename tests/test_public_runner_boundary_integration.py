from __future__ import annotations

import re
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
WORKFLOW=ROOT / ".github/workflows/nightly-multi-agent-research-v3.yml"
SHA_REF=re.compile(r"OPERATIONS_RESEARCH_REF:\s*([0-9a-f]{40})")

def test_nightly_private_checkout_boundary_is_explicit():
    text=WORKFLOW.read_text(encoding="utf-8")
    assert SHA_REF.search(text)
    assert "OPERATIONS_REPOSITORY: Z-Solo-King/operations" in text
    assert 'test -n "${OPERATIONS_APP_PRIVATE_KEY:-}"' in text
    assert 'test "$(git -C "$RUNNER_TEMP/operations-research" rev-parse HEAD)" = "$OPERATIONS_RESEARCH_REF"' in text
    assert 'rm -rf "$RUNNER_TEMP/operations-research"' in text
    assert "--crossfire" in text

def test_nightly_artifacts_never_target_private_checkout():
    text=WORKFLOW.read_text(encoding="utf-8")
    for name in ("lane 0","lane 1","lane 2"):
        assert f"name: Upload nightly research {name}" in text
    for line in text.splitlines():
        if line.strip().startswith("path:") or line.strip().startswith(".runtime/nightly-lane-"):
            assert "$RUNNER_TEMP/operations-research" not in line
            assert "private-agent" not in line.lower()