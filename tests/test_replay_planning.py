from backend.intelligence.contracts import ResearchContract
from backend.intelligence.planner_engine import create_task_plan
from backend.intelligence.replay import make_replay_bundle, replay_compatible


def test_replay_bundle_is_stable_for_same_inputs():
    contract = ResearchContract(question="Compare two models")
    plan = create_task_plan(contract)
    a = make_replay_bundle(contract, plan, capability_version="c1", policy_version="p1",
                           source_profile_version="s1", planner_version="1", created_at="t")
    b = make_replay_bundle(contract, plan, capability_version="c1", policy_version="p1",
                           source_profile_version="s1", planner_version="1", created_at="t")
    assert a == b
    assert replay_compatible(a, capability_version="c1", policy_version="p1", source_profile_version="s1")


def test_replay_bundle_rejects_context_drift():
    contract = ResearchContract(question="What is the current version?")
    plan = create_task_plan(contract)
    bundle = make_replay_bundle(contract, plan, capability_version="c1", policy_version="p1",
                                source_profile_version="s1", planner_version="1", created_at="t")
    assert not replay_compatible(bundle, capability_version="c2", policy_version="p1", source_profile_version="s1")
