from backend.intelligence.claims import Claim
from backend.intelligence.relationships import EvidenceRelation


def test_claim_and_relationship():
    claim = Claim(
        claim_id="claim-001",
        text="Evidence should be traceable.",
    )

    assert claim.claim_id == "claim-001"
    assert claim.text == "Evidence should be traceable."
    assert EvidenceRelation.SUPPORTS.value == "supports"
