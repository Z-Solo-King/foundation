from pathlib import Path
import sys

ROOT=Path(__file__).parents[1]
sys.path.insert(0,str(ROOT/"tools"))
import validate_workflow_authority as validator

def test_current_workflows_satisfy_authority_policy():
    errors=validator.validate()
    assert errors == [], "\n".join(errors)

def test_public_feed_workflows_are_explicitly_classified():
    text=(ROOT/"docs"/"WORKFLOW_AUTHORITY_REGISTRY.json").read_text(encoding="utf-8")
    assert "public_feed_workflows" in text
    assert "native-google-feed-hunt.yml" in text
    assert "woocommerce-clean-recovery.yml" in text

def test_privileged_policy_forbids_pr_triggers():
    text=(ROOT/"docs"/"WORKFLOW_AUTHORITY_REGISTRY.json").read_text(encoding="utf-8")
    assert "pull_request_target" in text
    assert "privileged_push_branch" in text
    assert "merge_group" in text


def test_trusted_workflow_run_source_is_registered():
    text=(ROOT/"docs"/"WORKFLOW_AUTHORITY_REGISTRY.json").read_text(encoding="utf-8")
    assert "trusted_workflow_run_sources" in text
    assert "live-nightly-research-canary.yml" in text
    assert "nightly multi-agent research" in text

def test_validator_inspects_merge_group_and_workflow_run():
    source=(ROOT/"tools"/"validate_workflow_authority.py").read_text(encoding="utf-8")
    assert '"merge_group"' in source
    assert '"workflow_run"' in source
    assert "workflow_run requires explicit trusted upstream registration" in source

def test_all_workflows_have_a_valid_trigger_mapping():
    import yaml
    workflow_dir = ROOT / ".github" / "workflows"
    for path in sorted(workflow_dir.glob("*.yml")) + sorted(workflow_dir.glob("*.yaml")):
        document = yaml.safe_load(path.read_text(encoding="utf-8"))
        trigger = document.get("on") if isinstance(document, dict) else None
        if trigger is None and isinstance(document, dict):
            trigger = document.get(True)
        assert isinstance(trigger, (dict, list, str)) or trigger is None, f"{path}: invalid workflow trigger mapping"
        assert trigger is not None, f"{path}: missing/invalid top-level on trigger"
