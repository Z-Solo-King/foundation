"""Tests for complete research execution pipeline."""

from backend.execution.engine import create_run, start_research, add_observation, verify_and_add_claim, complete_research, summarize_research
from backend.intelligence.contracts import ResearchContract, ResearchPlan
from backend.intelligence.observations import Observation, EvidenceSpan
from backend.intelligence.certificates import create_certificate
from backend.intelligence.claims import Claim
from backend.intelligence.lineage import SourceLineage
from backend.intelligence.verifier import EvidenceVerifier
from backend.execution.resources import ResourceBudget


def test_research_run_lifecycle():
    contract = ResearchContract(question="Is AI useful?")
    plan = ResearchPlan(question="Is AI useful?", stages=("discover", "collect", "verify", "synthesize"), source_budget=5, evidence_budget=10)
    run = start_research(create_run("run-1", contract, plan))
    assert run.status == "running"
    run = complete_research(run, success=True)
    assert run.status == "completed" and run.completed_at is not None


def test_add_observation_consumes_budget():
    contract = ResearchContract(question="test")
    plan = ResearchPlan(question="test", stages=(), source_budget=5, evidence_budget=5)
    run = create_run("run-1", contract, plan)
    budget = ResourceBudget(evidence_items=3)
    run = add_observation(run, Observation.create("o1", "s1", "https://example.com", "Content 1"), budget)
    assert len(run.observations) == 1 and budget.remaining()["evidence_items"] == 2
    run = add_observation(run, Observation.create("o2", "s1", "https://example.com", "Content 2"), budget)
    assert len(run.observations) == 2 and budget.remaining()["evidence_items"] == 1


def test_verify_and_add_claim():
    contract = ResearchContract(question="test")
    plan = ResearchPlan(question="test", stages=(), source_budget=5, evidence_budget=10)
    run = create_run("run-1", contract, plan)
    obs = Observation.create("o1", "s1", "https://example.com", "Yes, AI is useful.")
    run = add_observation(run, obs, ResourceBudget())
    cert = create_certificate(obs, EvidenceSpan("o1", 5, 7))
    claim = Claim.create("c1", "AI is useful.")
    run = verify_and_add_claim(run, claim, (cert,), EvidenceVerifier(), {"s1": SourceLineage("s1", "family-a")})
    assert len(run.verified_claims) == 1 and run.verified_claims[0][0].claim_id == "c1"


def test_summarize_research():
    contract = ResearchContract(question="What is the answer?")
    plan = ResearchPlan(question="What is the answer?", stages=(), source_budget=5, evidence_budget=10)
    run = start_research(create_run("run-1", contract, plan))
    obs = Observation.create("o1", "s1", "https://example.com", "The answer is 42.")
    run = add_observation(run, obs, ResourceBudget())
    cert = create_certificate(obs, EvidenceSpan("o1", 15, 17))
    run = verify_and_add_claim(run, Claim.create("c1", "The answer is 42."), (cert,), EvidenceVerifier(), {"s1": SourceLineage("s1", "family-a")})
    run = complete_research(run)
    summary = summarize_research(run)
    assert summary["run_id"] == "run-1" and summary["status"] == "completed" and summary["observations"] == 1


def test_synthesis_with_corroborated_claims():
    contract = ResearchContract(question="Is X true?")
    plan = ResearchPlan(question="Is X true?", stages=(), source_budget=5, evidence_budget=10)
    run = start_research(create_run("run-1", contract, plan))
    obs1 = Observation.create("o1", "s1", "https://a.com", "X is true.")
    obs2 = Observation.create("o2", "s2", "https://b.com", "X is definitely true.")
    run = add_observation(run, obs1, ResourceBudget(evidence_items=100))
    run = add_observation(run, obs2, ResourceBudget(evidence_items=100))
    cert1 = create_certificate(obs1, EvidenceSpan("o1", 0, 1))
    cert2 = create_certificate(obs2, EvidenceSpan("o2", 0, 1))
    run = verify_and_add_claim(run, Claim.create("c1", "X is true."), (cert1, cert2), EvidenceVerifier(), {"s1": SourceLineage("s1", "family-a"), "s2": SourceLineage("s2", "family-b")})
    run = complete_research(run)
    from backend.execution.synthesis import ResearchSynthesizer
    result = ResearchSynthesizer().synthesize(run)
    assert result.question == "Is X true?" and result.confidence == "high" and len(result.evidence_chain) == 2
