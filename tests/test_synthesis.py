"""Tests for research synthesis."""

import pytest
from backend.execution.engine import create_run, start_research, complete_research
from backend.execution.synthesis import ResearchSynthesizer
from backend.intelligence.contracts import ResearchContract, ResearchPlan
from backend.execution.resources import ResourceBudget


def test_synthesizer_no_claims():
    """Synthesizer handles run with no verified claims."""
    contract = ResearchContract(question="What is X?")
    plan = ResearchPlan(
        question="What is X?",
        stages=(),
        source_budget=5,
        evidence_budget=10,
    )
    run = create_run("run-1", contract, plan)
    run = start_research(run)
    run = complete_research(run)
    
    synthesizer = ResearchSynthesizer()
    result = synthesizer.synthesize(run)
    
    assert "no evidence" in result.answer.lower()
    assert result.confidence == "unknown"
