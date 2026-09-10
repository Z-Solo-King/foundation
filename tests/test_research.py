from backend.research import ResearchContract


def test_research_contract_defaults():
    contract = ResearchContract(question="Test question")
    assert contract.depth == "standard"
    assert contract.require_citations is True
