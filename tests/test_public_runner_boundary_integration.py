from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github/workflows/nightly-multi-agent-research-v3.yml"
SHA_REF = re.compile(r"OPERATIONS_RESEARCH_REF:\s*([0-9a-f]{40})")
UPLOAD_STEP = re.compile(r"(?ms)^      - uses: actions/upload-artifact@.*?(?=^      - |\Z)")


def test_nightly_private_checkout_boundary_is_explicit() -> None:
    text = WORKFLOW.read_text(encoding="utf-8")
    match = SHA_REF.search(text)
    assert match, "nightly workflow must pin Operations to an immutable commit SHA"
    assert "OPERATIONS_REPOSITORY: Z-Solo-King/operations" in text
    assert 'test -n "${OPERATIONS_APP_PRIVATE_KEY:-}"' in text
    assert 'test "$(git -C "$RUNNER_TEMP/operations-research" rev-parse HEAD)" = "$OPERATIONS_RESEARCH_REF"' in text
    assert 'rm -rf "$RUNNER_TEMP/operations-research"' in text


def test_nightly_artifacts_never_target_private_checkout() -> None:
    text = WORKFLOW.read_text(encoding="utf-8")
    upload_steps = UPLOAD_STEP.findall(text)
    lane_steps = [step for step in upload_steps if "name: nightly-research-lane-" in step]
    assert lane_steps, "nightly research lane artifacts must remain explicit"
    for step in lane_steps:
        path_section = step.split("path:", 1)[1] if "path:" in step else ""
        assert "$RUNNER_TEMP/operations-research" not in path_section
        assert "private-agent" not in path_section.lower()


def test_public_boundary_validator_is_part_of_repository_contract() -> None:
    validator = ROOT / "benchmark/public_runner_boundary.py"
    text = validator.read_text(encoding="utf-8")
    assert 'SCHEMA = "nightly-research-program/v1"' in text
    assert "_ALLOWED_TOP_LEVEL" in text
    assert "_ALLOWED_FINDING" in text
    assert "_SECRET_PATTERN" in text
    assert "_PRIVATE_HOSTS" in text
    assert "validate_jsonl" in text
