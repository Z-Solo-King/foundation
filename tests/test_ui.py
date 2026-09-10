"""Tests for research UI."""

import pytest
from backend.frontend.ui import ResearchUI
from backend.execution.engine import create_run, start_research, complete_research
from backend.intelligence.contracts import ResearchContract, ResearchPlan
from backend.intelligence.observations import Observation, EvidenceSpan
from backend.intelligence.certificates import create_certificate
from backend.intelligence.claims import Claim
from backend.intelligence.lineage import SourceLineage
from backend.intelligence.verifier import EvidenceVerifier
from backend.execution.resources import ResourceBudget


def test_ui_health_check():
    """UI renders health check."""
    ui = ResearchUI()
    health = ui.render_health_check()
    assert health["ok"] is True
    assert health["app"] == "Research Intelligence Engine"


def test_ui_readiness_check():
    """UI renders readiness check."""
    ui = ResearchUI()
    readiness = ui.render_readiness_check()
    assert readiness["ready"] is True


def test_ui_research_form_schema():
    """UI renders research form schema."""
    ui = ResearchUI()
    form = ui.render_research_form()
    assert "question" in form["form"]
    assert "depth" in form["form"]
    assert form["form"]["depth"]["options"] == ["quick", "standard", "deep"]


def test_ui_submit_research():
    """UI submits research contract."""
    ui = ResearchUI()
    response = ui.submit_research(
        question="What is the answer?",
        depth="quick",
    )
    assert response["ok"] is True
    assert response["run_id"] is not None


def test_ui_render_run_summary():
    """UI renders run summary."""
    ui = ResearchUI()
    
    contract = ResearchContract(question="test")
    plan = ResearchPlan(
        question="test",
        stages=(),
        source_budget=5,
        evidence_budget=10,
    )
    run = create_run("run-1", contract, plan)
    run = start_research(run)
    run = complete_research(run)
    
    summary = ui.render_run_summary(run)
    assert summary["run_id"] == "run-1"
    assert summary["status"] == "completed"


def test_ui_render_synthesis_result():
    """UI renders synthesis result with citations."""
    ui = ResearchUI()
    
    contract = ResearchContract(question="Is X true?")
    plan = ResearchPlan(
        question="Is X true?",
        stages=(),
        source_budget=5,
        evidence_budget=10,
    )
    run = create_run("run-1", contract, plan)
    run = start_research(run)
    
    obs = Observation.create("o1", "s1", "https://example.com", "X is true.")
    run = backend.execution.engine.add_observation(run, obs, ResourceBudget(evidence_items=100))
    
    span = EvidenceSpan("o1", 0, 1)
    cert = create_certificate(obs, span)
    claim = Claim.create("c1", "X is true.")
    lineage = SourceLineage("s1", "family-a")
    
    verifier = EvidenceVerifier()
    run = backend.execution.engine.verify_and_add_claim(run, claim, (cert,), verifier, {"s1": lineage})
    run = complete_research(run)
    
    result = ui.render_synthesis_result(run)
    assert result["question"] == "Is X true?"
    assert result["confidence"] in ["high", "medium", "low", "unknown"]
    assert len(result["evidence_chain"]) > 0
