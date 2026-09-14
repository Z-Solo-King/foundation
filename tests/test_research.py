import pytest

from backend.intelligence.contracts import ResearchContract


def test_research_contract_defaults():
    contract = ResearchContract(question="Test question")
    assert contract.depth == "standard"
    assert contract.require_citations is True


def test_research_contract_rejects_blank_question():
    with pytest.raises(ValueError, match="question must not be empty"):
        ResearchContract(question="   ").validate()


def test_research_contract_rejects_nonpositive_source_budget():
    with pytest.raises(ValueError, match="max_sources must be positive"):
        ResearchContract(question="Test question", max_sources=0).validate()


def test_research_contract_rejects_nonpositive_evidence_budget():
    with pytest.raises(ValueError, match="max_evidence_items must be positive"):
        ResearchContract(question="Test question", max_evidence_items=0).validate()
