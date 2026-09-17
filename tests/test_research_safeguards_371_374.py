from datetime import datetime, timezone, timedelta

from foundation_core.stage_receipt import StageReceipt, can_resume, validate_chain
from foundation_core.token_efficiency import EfficiencyGate, TokenEfficiencyObservation, compare_efficiency


def receipt(**overrides):
    values = dict(request_fingerprint="req", stage="price", input_fingerprint="in", output_fingerprint="out", method="deterministic", resource_units=2)
    values.update(overrides)
    return StageReceipt(**values)


def observation(**overrides):
    values = dict(planned_context_units=10, retained_evidence_units=8, dropped_evidence_units=2, duplicate_evidence_dropped=0, estimated_input_tokens=100, estimated_output_tokens=100, model_calls=1, accepted=True)
    values.update(overrides)
    return TokenEfficiencyObservation(**values)


def test_expired_receipt_cannot_resume():
    now = datetime(2026, 9, 17, tzinfo=timezone.utc)
    old = (now - timedelta(hours=1)).isoformat()
    expired = (now - timedelta(minutes=1)).isoformat()
    assert not can_resume(receipt(created_at=old, expires_at=expired), request_fingerprint="req", input_fingerprint="in", now=now)


def test_unexpired_receipt_can_resume():
    now = datetime(2026, 9, 17, tzinfo=timezone.utc)
    assert can_resume(receipt(expires_at=(now + timedelta(minutes=1)).isoformat()), request_fingerprint="req", input_fingerprint="in", now=now)


def test_chain_resource_budget_is_enforced():
    first = receipt(resource_units=4)
    second = receipt(parent_receipt_fingerprint=first.fingerprint(), resource_units=5)
    chain = (first, second)
    assert validate_chain(chain, max_resource_units=9)
    assert not validate_chain(chain, max_resource_units=8)


def test_output_floor_blocks_degenerate_candidate():
    baseline = observation(estimated_output_tokens=100)
    candidate = observation(estimated_output_tokens=40)
    ok, reason = compare_efficiency(baseline, candidate, gate=EfficiencyGate(min_output_tokens_ratio=0.5))
    assert not ok
    assert "output-token" in reason


def test_context_amplification_gate_blocks_hidden_context_growth():
    baseline = observation(estimated_input_tokens=100, estimated_output_tokens=100)
    candidate = observation(estimated_input_tokens=200, estimated_output_tokens=100)
    ok, reason = compare_efficiency(baseline, candidate, gate=EfficiencyGate(max_input_token_growth_ratio=1.0, max_total_token_growth_ratio=1.0, max_context_amplification_ratio=2.5))
    assert not ok
    assert "context amplification" in reason
