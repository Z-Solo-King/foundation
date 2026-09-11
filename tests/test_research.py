from backend.intelligence.contracts import ResearchContract


def test_research_contract_defaults():
    contract = ResearchContract(question="Test question")
    assert contract.depth == "standard"
    assert contract.require_citations is True
