from foundation_core.token_efficiency import EfficiencyGate, TokenEfficiencyObservation, compare_efficiency


def observation(*, input_tokens: int, output_tokens: int) -> TokenEfficiencyObservation:
    return TokenEfficiencyObservation(
        planned_context_units=10,
        retained_evidence_units=10,
        dropped_evidence_units=0,
        duplicate_evidence_dropped=0,
        estimated_input_tokens=input_tokens,
        estimated_output_tokens=output_tokens,
        model_calls=1,
        accepted=True,
    )


def test_context_amplification_ratio_rejects_ballooning_context():
    baseline = observation(input_tokens=100, output_tokens=100)
    candidate = observation(input_tokens=200, output_tokens=50)

    accepted, reason = compare_efficiency(
        baseline,
        candidate,
        gate=EfficiencyGate(
            max_input_token_growth_ratio=1.0,
            max_total_token_growth_ratio=1.0,
            max_context_amplification_ratio=4.0,
        ),
    )

    assert not accepted
    assert reason == "candidate context amplification exceeds gate"


def test_context_amplification_ratio_can_be_disabled():
    baseline = observation(input_tokens=100, output_tokens=100)
    candidate = observation(input_tokens=90, output_tokens=60)

    accepted, reason = compare_efficiency(
        baseline,
        candidate,
        gate=EfficiencyGate(max_context_amplification_ratio=None),
    )

    assert accepted
    assert reason == "candidate accepted with non-increasing token use"


def test_context_amplification_gate_rejects_invalid_threshold():
    gate = EfficiencyGate(max_context_amplification_ratio=0.0)
    try:
        gate.validate()
    except ValueError as exc:
        assert "max_context_amplification_ratio" in str(exc)
    else:
        raise AssertionError("invalid amplification threshold should fail validation")
