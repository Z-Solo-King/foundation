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
