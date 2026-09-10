"""Tests for research UI."""

from backend.frontend.ui import ResearchUI
from backend.execution.engine import create_run, start_research, add_observation, verify_and_add_claim, complete_research
from backend.intelligence.contracts import ResearchContract, ResearchPlan
from backend.intelligence.observations import Observation, EvidenceSpan
from backend.intelligence.certificates import create_certificate
from backend.intelligence.claims import Claim
from backend.intelligence.lineage import SourceLineage
from backend.intelligence.verifier import EvidenceVerifier
from backend.execution.resources import ResourceBudget


def test_ui_health_check():
    health = ResearchUI().render_health_check()
    assert health["ok"] is True and health["app"] == "Research Intelligence Engine"


def test_ui_readiness_check():
    assert ResearchUI().render_readiness_check()["ready"] is True


def test_ui_research_form_schema():
    form = ResearchUI().render_research_form()
    assert "question" in form["form"] and "depth" in form["form"]
    assert form["form"]["depth"]["options"] == ["quick", "standard", "deep"]


def test_ui_submit_research():
    response = ResearchUI().submit_research(question="What is the answer?", depth="quick")
    assert response["ok"] is True and response["run_id"] is not None


def test_ui_render_run_summary():
    ui = ResearchUI()
    contract = ResearchContract(question="test")
    plan = ResearchPlan(question="test", stages=(), source_budget=5, evidence_budget=10)
    run = complete_research(start_research(create_run("run-1", contract, plan)))
    summary = ui.render_run_summary(run)
    assert summary["run_id"] == "run-1" and summary["status"] == "completed"


def test_ui_render_synthesis_result():
    ui = ResearchUI()
    contract = ResearchContract(question="Is X true?")
    plan = ResearchPlan(question="Is X true?", stages=(), source_budget=5, evidence_budget=10)
    run = start_research(create_run("run-1", contract, plan))
    obs = Observation.create("o1", "s1", "https://example.com", "X is true.")
    run = add_observation(run, obs, ResourceBudget(evidence_items=100))
    cert = create_certificate(obs, EvidenceSpan("o1", 0, 1))
    run = verify_and_add_claim(run, Claim.create("c1", "X is true."), (cert,), EvidenceVerifier(), {"s1": SourceLineage("s1", "family-a")})
    run = complete_research(run)
    result = ui.render_synthesis_result(run)
    assert result["question"] == "Is X true?"
    assert result["confidence"] in ["high", "medium", "low", "unknown"]
    assert result["evidence_chain"]
