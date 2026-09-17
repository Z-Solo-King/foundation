from foundation_core.token_efficiency import (
    EfficiencyGate,
    TokenEfficiencyObservation,
    compare_efficiency,
)


def obs(*, input_tokens=100, output_tokens=100, accepted=True, retained=10, dropped=0, cache_hits=0, model_calls=1):
    return TokenEfficiencyObservation(
        planned_context_units=max(1, retained + dropped),
        retained_evidence_units=retained,
        dropped_evidence_units=dropped,
        duplicate_evidence_dropped=0,
        estimated_input_tokens=input_tokens,
        estimated_output_tokens=output_tokens,
        model_calls=model_calls,
        cache_hits=cache_hits,
        accepted=accepted,
    )


def test_output_floor_rejects_truncated_non_increasing_candidate():
    baseline = obs(output_tokens=100)
    candidate = obs(input_tokens=80, output_tokens=40)
    gate = EfficiencyGate(min_output_ratio=0.75)

    accepted, reason = compare_efficiency(baseline, candidate, gate=gate)

    assert not accepted
    assert reason == "candidate output size is below configured floor"


def test_output_floor_allows_candidate_at_floor():
    baseline = obs(output_tokens=100)
    candidate = obs(input_tokens=80, output_tokens=80)
    gate = EfficiencyGate(min_output_ratio=0.80)

    accepted, reason = compare_efficiency(baseline, candidate, gate=gate)

    assert accepted
    assert reason == "candidate accepted with non-increasing token use"


def test_absolute_floor_handles_small_baseline():
    baseline = obs(output_tokens=1)
    candidate = obs(input_tokens=1, output_tokens=0)
    gate = EfficiencyGate(min_output_tokens=1)

    accepted, reason = compare_efficiency(baseline, candidate, gate=gate)

    assert not accepted
    assert reason == "candidate output size is below configured floor"


def test_output_floor_zero_keeps_non_increasing_path():
    baseline = obs(output_tokens=100)
    candidate = obs(input_tokens=80, output_tokens=1)
    gate = EfficiencyGate()

    accepted, reason = compare_efficiency(baseline, candidate, gate=gate)

    assert accepted
    assert reason == "candidate accepted with non-increasing token use"


def test_negative_absolute_floor_is_rejected():
    gate = EfficiencyGate(min_output_tokens=-1)
    try:
        gate.validate()
    except ValueError as exc:
        assert "min_output_tokens" in str(exc)
    else:
        raise AssertionError("negative output floor should fail validation")


def test_context_amplification_gate_rejects_balloons():
    baseline = obs(input_tokens=100, output_tokens=100)
    candidate = obs(input_tokens=900, output_tokens=100)
    gate = EfficiencyGate(
        max_input_token_growth_ratio=10.0,
        max_total_token_growth_ratio=10.0,
        max_context_amplification_ratio=5.0,
    )

    accepted, reason = compare_efficiency(baseline, candidate, gate=gate)

    assert not accepted
    assert reason == "candidate context amplification exceeds gate"


def test_context_amplification_gate_allows_bounded_candidate():
    baseline = obs(input_tokens=100, output_tokens=100)
    candidate = obs(input_tokens=110, output_tokens=100)
    gate = EfficiencyGate(max_context_amplification_ratio=3.0)

    accepted, reason = compare_efficiency(baseline, candidate, gate=gate)

    assert accepted
    assert reason == "candidate accepted with non-increasing token use"


def test_context_amplification_gate_requires_finite_positive_limit():
    for value in (0.0, -1.0, float("inf")):
        gate = EfficiencyGate(max_context_amplification_ratio=value)
        try:
            gate.validate()
        except ValueError as exc:
            assert "max_context_amplification_ratio" in str(exc)
        else:
            raise AssertionError("invalid amplification limit should fail validation")


def test_output_floor_configuration_is_validated():
    gate = EfficiencyGate(min_output_ratio=1.1)
    try:
        gate.validate()
    except ValueError as exc:
        assert "min_output_ratio" in str(exc)
    else:
        raise AssertionError("invalid output ratio should fail validation")


def test_extra_token_path_keeps_existing_evidence_rule():
    baseline = obs(output_tokens=50, retained=5, dropped=5)
    candidate = obs(input_tokens=105, output_tokens=55, retained=10, dropped=0)
    gate = EfficiencyGate(min_output_ratio=0.95)

    accepted, reason = compare_efficiency(baseline, candidate, gate=gate)

    assert accepted
    assert reason == "candidate spends limited extra tokens for better evidence retention"
