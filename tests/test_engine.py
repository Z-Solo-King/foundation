"""Tests for complete research execution pipeline."""

import pytest
from datetime import datetime, timezone

from backend.execution.engine import (
    create_run,
    start_research,
    add_observation,
    add_claim,
    verify_and_add_claim,
    complete_research,
    summarize_research,
)
from backend.execution.synthesis import ResearchSynthesizer
from backend.intelligence.contracts import ResearchContract, ResearchPlan
from backend.intelligence.observations import Observation, EvidenceSpan
from backend.intelligence.certificates import create_certificate
from backend.intelligence.claims import Claim
from backend.intelligence.lineage import SourceLineage
from backend.intelligence.verifier import EvidenceVerifier
from backend.execution.resources import ResourceBudget


def test_research_run_lifecycle():
    """Test complete research run lifecycle."""
    contract = ResearchContract(question="Is AI useful?")
    plan = ResearchPlan(
        question="Is AI useful?",
        stages=("discover", "collect", "verify", "synthesize"),
        source_budget=5,
        evidence_budget=10,
    )
    
    run = create_run("run-1", contract, plan)
    assert run.status == "planned"
    assert run.started_at is None
    
    run = start_research(run)
    assert run.status == "running"
    assert run.started_at is not None
    
    run = complete_research(run, success=True)
    assert run.status == "completed"
    assert run.completed_at is not None


def test_add_observation_consumes_budget():
    """Adding observation consumes evidence budget."""
    contract = ResearchContract(question="test")
    plan = ResearchPlan(
        question="test",
        stages=(),
        source_budget=5,
        evidence_budget=5,
    )
    run = create_run("run-1", contract, plan)
    budget = ResourceBudget(evidence_items=3)
    
    obs1 = Observation.create("o1", "s1", "https://example.com", "Content 1")
    run = add_observation(run, obs1, budget)
    assert len(run.observations) == 1
    assert budget.remaining()["evidence_items"] == 2
    
    obs2 = Observation.create("o2", "s1", "https://example.com", "Content 2")
    run = add_observation(run, obs2, budget)
    assert len(run.observations) == 2
    assert budget.remaining()["evidence_items"] == 1


def test_verify_and_add_claim():
    """Claims are verified and added to run."""
    contract = ResearchContract(question="test")
    plan = ResearchPlan(
        question="test",
        stages=(),
        source_budget=5,
        evidence_budget=10,
    )
    run = create_run("run-1", contract, plan)
    
    obs = Observation.create("o1", "s1", "https://example.com", "Yes, AI is useful.")
    run = add_observation(run, obs, ResourceBudget())
    
    span = EvidenceSpan("o1", 5, 7)
    cert = create_certificate(obs, span)
    
    claim = Claim.create("c1", "AI is useful.")
    lineage = SourceLineage("s1", "family-a")
    
    verifier = EvidenceVerifier()
    run = verify_and_add_claim(run, claim, (cert,), verifier, {"s1": lineage})
    
    assert len(run.verified_claims) == 1
    assert run.verified_claims[0][0].claim_id == "c1"


def test_summarize_research():
    """Research summary includes statistics and findings."""
    contract = ResearchContract(question="What is the answer?")
    plan = ResearchPlan(
        question="What is the answer?",
        stages=(),
        source_budget=5,
        evidence_budget=10,
    )
    run = create_run("run-1", contract, plan)
    run = start_research(run)
    
    obs = Observation.create("o1", "s1", "https://example.com", "The answer is 42.")
    run = add_observation(run, obs, ResourceBudget())
    
    span = EvidenceSpan("o1", 16, 18)
    cert = create_certificate(obs, span)
    claim = Claim.create("c1", "The answer is 42.")
    lineage = SourceLineage("s1", "family-a")
    
    verifier = EvidenceVerifier()
    run = verify_and_add_claim(run, claim, (cert,), verifier, {"s1": lineage})
    run = complete_research(run)
    
    summary = summarize_research(run)
    assert summary["run_id"] == "run-1"
    assert summary["status"] == "completed"
    assert summary["question"] == "What is the answer?"
    assert summary["observations"] == 1
    assert summary["claims_verified"] == 1


def test_synthesis_with_corroborated_claims():
    """Synthesizer produces high-confidence answer from corroborated claims."""
    contract = ResearchContract(question="Is X true?")
    plan = ResearchPlan(
        question="Is X true?",
        stages=(),
        source_budget=5,
        evidence_budget=10,
    )
    run = create_run("run-1", contract, plan)
    run = start_research(run)
    
    # Add two observations from different families
    obs1 = Observation.create("o1", "s1", "https://a.com", "X is true.")
    obs2 = Observation.create("o2", "s2", "https://b.com", "X is definitely true.")
    run = add_observation(run, obs1, ResourceBudget(evidence_items=100))
    run = add_observation(run, obs2, ResourceBudget(evidence_items=100))
    
    span1 = EvidenceSpan("o1", 0, 1)
    cert1 = create_certificate(obs1, span1)
    span2 = EvidenceSpan("o2", 0, 1)
    cert2 = create_certificate(obs2, span2)
    
    claim = Claim.create("c1", "X is true.")
    lineage1 = SourceLineage("s1", "family-a")
    lineage2 = SourceLineage("s2", "family-b")
    
    verifier = EvidenceVerifier()
    run = verify_and_add_claim(run, claim, (cert1, cert2), verifier, {"s1": lineage1, "s2": lineage2})
    run = complete_research(run)
    
    synthesizer = ResearchSynthesizer()
    result = synthesizer.synthesize(run)
    
    assert result.question == "Is X true?"
    assert result.confidence == "high"
    assert len(result.evidence_chain) == 2
