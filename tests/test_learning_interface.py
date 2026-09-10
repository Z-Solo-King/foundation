from backend.learning.interface import BehaviorChangeProposal, BehaviorEvaluation


def test_public_learning_interface_is_data_only():
    proposal = BehaviorChangeProposal("c1", "improve extraction", "extractor")
    evaluation = BehaviorEvaluation("c1", 90.0, 91.0, 0.0, 0.01, 50)
    assert proposal.affected_component == "extractor"
    assert evaluation.as_promotion_evidence()["benchmark_count"] == 50
