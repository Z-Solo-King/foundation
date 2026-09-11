from backend.planner import create_plan
from backend.intelligence.contracts import ResearchContract


def test_create_plan():
    contract = ResearchContract(question="What is machine learning?")
    plan = create_plan(contract)

    assert plan.question == "What is machine learning?"
    assert "discover_sources" in plan.stages
    assert "verify_evidence" in plan.stages
