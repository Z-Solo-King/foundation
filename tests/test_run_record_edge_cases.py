import math
import pytest
from backend.run_record import ChatbotRunRecord
from backend.stage_receipt import StageReceipt
from backend.token_efficiency import TokenEfficiencyObservation, compare_efficiency
from tests.test_public_chatbot_primitives import _record, _receipt


def test_run_record_remaining_validation_guards():
    with pytest.raises(ValueError): _record(stages=()).validate()
    with pytest.raises(ValueError): _record(stages=(_receipt(), _receipt("fetch", "wrong"))).validate()
    mismatched=StageReceipt("other","plan","in","out","local")
    with pytest.raises(ValueError): _record(stages=(mismatched,)).validate()


def test_stage_receipt_bounded_length_guard():
    with pytest.raises(ValueError): StageReceipt("r"*129,"stage","in","out","local")


def test_token_efficiency_nonfinite_growth_guard():
    baseline=TokenEfficiencyObservation(10,1,0,0,1,0,1,0,0,True)
    candidate=TokenEfficiencyObservation(10,1,0,0,math.inf,0,1,0,0,True)
    assert compare_efficiency(baseline,candidate)[0] is False
