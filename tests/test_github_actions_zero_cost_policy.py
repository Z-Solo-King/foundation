from __future__ import annotations

from pathlib import Path
import tempfile

from scripts.validate_github_actions_zero_cost import (
    load_policy,
    validate_policy_document,
    validate_workflow_text,
)


ROOT = Path(__file__).parents[1]


def test_zero_cost_policy_document_is_valid() -> None:
    validate_policy_document()
    policy = load_policy()
    assert policy["zero_cost_invariants"]["max_additional_cost_usd"] == 0
    assert policy["action_policy"]["full_sha_required"] is True
    assert policy["action_policy"]["unknown_action_ref_policy"] == "deny"


def test_current_action_allowlist_is_immutable() -> None:
    policy = load_policy()
    for ref in policy["action_policy"]["allowed_action_refs"]:
        action, sha = ref.rsplit("@", 1)
        assert action
        assert len(sha) == 40
        assert all(char in "0123456789abcdefABCDEF" for char in sha)


def test_unknown_action_and_paid_runner_are_rejected() -> None:
    policy = load_policy()
    text = """
jobs:
  bad:
    runs-on: ubuntu-latest-xl
    steps:
      - uses: example/vendor-action@0123456789abcdef0123456789abcdef01234567
"""
    errors = validate_workflow_text(Path("bad.yml"), text, policy)
    assert any("outside the $0 allowlist" in error for error in errors)
    assert any("not in the approved $0 allowlist" in error for error in errors)


def test_non_sha_action_is_rejected() -> None:
    policy = load_policy()
    text = """
jobs:
  bad:
    runs-on: ubuntu-latest
    steps:
      - uses: example/vendor-action@v1
"""
    errors = validate_workflow_text(Path("bad.yml"), text, policy)
    assert any("does not use a full 40-hex commit SHA" in error for error in errors)


def test_docker_action_is_rejected() -> None:
    policy = load_policy()
    text = """
jobs:
  bad:
    runs-on: ubuntu-latest
    steps:
      - uses: docker://example/image:latest
"""
    errors = validate_workflow_text(Path("bad.yml"), text, policy)
    assert any("docker Actions are forbidden" in error for error in errors)


def test_zizmor_paid_mode_is_rejected() -> None:
    policy = load_policy()
    text = """
jobs:
  security:
    runs-on: ubuntu-latest
    steps:
      - uses: zizmorcore/zizmor-action@cc914d7f3750a2d13d75c7f184a1060aa0e9d482
        with:
          advanced-security: true
"""
    errors = validate_workflow_text(Path("bad.yml"), text, policy)
    assert any("advanced-security: false" in error for error in errors)


def test_scorecard_publish_is_rejected() -> None:
    policy = load_policy()
    text = """
jobs:
  security:
    runs-on: ubuntu-latest
    steps:
      - uses: ossf/scorecard-action@2d1146689b8cda280b9bc96326124645441f03bc
        with:
          publish_results: true
"""
    errors = validate_workflow_text(Path("bad.yml"), text, policy)
    assert any("Scorecard publishing" in error for error in errors)


def test_current_static_security_workflow_passes_zero_cost_rules() -> None:
    path = ROOT / ".github" / "workflows" / "actions-static-analysis.yml"
    errors = validate_workflow_text(path, path.read_text(encoding="utf-8"), load_policy())
    assert errors == []
