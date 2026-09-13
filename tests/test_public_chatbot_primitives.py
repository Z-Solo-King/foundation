import pytest

from backend.run_record import (
    ChatbotRunRecord,
    EvidenceSelectionMetrics,
    ResourceUsage,
    RunResult,
    TokenEfficiencyMetrics,
)
from backend.stage_receipt import StageReceipt, can_resume, fingerprint, validate_chain
from backend.token_efficiency import EfficiencyGate, TokenEfficiencyObservation, compare_efficiency


def _receipt(stage="plan", parent=None, *, resume_eligible=True, status="completed"):
    return StageReceipt(
        "req", stage, fingerprint(stage), fingerprint({stage: True}), "local",
        parent_receipt_fingerprint=parent, resume_eligible=resume_eligible, status=status,
    )


def _record(**kwargs):
    first = _receipt()
    return ChatbotRunRecord(
        schema_version="1",
        run_id="run-1",
        created_at="2026-09-13T00:00:00Z",
        request_fingerprint="req",
        intent={},
        method_selected="deterministic",
        method_reason="test",
        stages=(first,),
        result=RunResult("success"),
        software={"version": "test"},
        resource_usage=ResourceUsage(),
        **kwargs,
    )


def test_stage_receipt_resume_and_chain():
    first = _receipt()
    second = _receipt("fetch", first.fingerprint())
    assert can_resume(first, request_fingerprint="req", input_fingerprint=first.input_fingerprint)
    assert not can_resume(first, request_fingerprint="other", input_fingerprint=first.input_fingerprint)
    assert not can_resume(_receipt(status="running"), request_fingerprint="req", input_fingerprint=first.input_fingerprint)
    assert not can_resume(_receipt(resume_eligible=False), request_fingerprint="req", input_fingerprint=first.input_fingerprint)
    assert validate_chain(())
    assert validate_chain((first, second))
    assert not validate_chain((first, _receipt("bad", "wrong")))
    assert not validate_chain((_receipt(resume_eligible=False),))
    assert not validate_chain((_receipt(), StageReceipt("other", "fetch", "in", "out", "local")))


def test_stage_receipt_rejects_bounds():
    with pytest.raises(ValueError):
        StageReceipt("", "stage", "in", "out", "local")
    for field in ("stage", "input_fingerprint", "output_fingerprint", "method", "provider", "status"):
        values = {"request_fingerprint": "req", "stage": "stage", "input_fingerprint": "in", "output_fingerprint": "out", "method": "local", "provider": "local", "status": "completed"}
        values[field] = ""
        with pytest.raises(ValueError):
            StageReceipt(**values)
    with pytest.raises(ValueError):
        StageReceipt("req", "stage", "in", "out", "local", resource_units=-1)
    with pytest.raises(ValueError):
        StageReceipt("req", "stage", "in", "out", "local", attempt=0)
    with pytest.raises(ValueError):
        StageReceipt("req", "stage", "in", "out", "local", parent_receipt_fingerprint="")


def test_token_efficiency_observation_and_gate_guards():
    base_values = dict(planned_context_units=10, retained_evidence_units=6, dropped_evidence_units=4, duplicate_evidence_dropped=1, estimated_input_tokens=100, estimated_output_tokens=50, model_calls=4, cache_hits=1, deterministic_steps=2, accepted=True)
    assert TokenEfficiencyObservation(0, 0, 0, 0, 0, 0, 0).evidence_retention_ratio == 1.0
    assert TokenEfficiencyObservation(**base_values).cache_hit_ratio == 0.25
    assert TokenEfficiencyObservation(**base_values).total_estimated_tokens == 150
    assert TokenEfficiencyObservation(**base_values).token_density() > 0
    assert TokenEfficiencyObservation(**{**base_values, "accepted": False}).token_density() == 0
    assert TokenEfficiencyObservation(**{**base_values, "estimated_input_tokens": 0, "estimated_output_tokens": 0}).token_density() == 0

    for field in ("planned_context_units", "retained_evidence_units", "dropped_evidence_units", "duplicate_evidence_dropped", "estimated_input_tokens", "estimated_output_tokens", "model_calls", "cache_hits", "deterministic_steps"):
        values = dict(base_values)
        values[field] = -1
        with pytest.raises(ValueError):
            TokenEfficiencyObservation(**values).validate()
    with pytest.raises(ValueError):
        TokenEfficiencyObservation(1, 1, 1, 0, 1, 1, 0).validate()
    for field in ("max_input_token_growth_ratio", "max_total_token_growth_ratio", "min_cache_hit_ratio"):
        values = {"max_input_token_growth_ratio": 0.1, "max_total_token_growth_ratio": 0.1, "min_cache_hit_ratio": 0.0}
        values[field] = 1.1
        with pytest.raises(ValueError):
            EfficiencyGate(**values).validate()


def test_token_efficiency_compare_all_gate_paths():
    baseline = TokenEfficiencyObservation(10, 6, 4, 1, 100, 50, 4, 1, 2, True)
    candidate_first = TokenEfficiencyObservation(10, 6, 4, 1, 100, 50, 4, 1, 2, True)
    baseline_not = TokenEfficiencyObservation(10, 6, 4, 1, 100, 50, 4, 1, 2, False)
    accepted = TokenEfficiencyObservation(10, 7, 3, 1, 100, 50, 4, 2, 2, True)
    cheaper = TokenEfficiencyObservation(10, 6, 4, 1, 90, 40, 4, 0, 2, True)
    input_growth = TokenEfficiencyObservation(10, 6, 4, 1, 112, 50, 4, 1, 2, True)
    total_growth = TokenEfficiencyObservation(10, 6, 4, 1, 100, 66, 4, 1, 2, True)
    low_cache = TokenEfficiencyObservation(10, 6, 4, 1, 100, 50, 4, 0, 2, True)
    extra_same_retention = TokenEfficiencyObservation(10, 6, 4, 1, 105, 50, 4, 1, 2, True)
    extra_better_retention = TokenEfficiencyObservation(10, 7, 3, 1, 105, 50, 4, 1, 2, True)

    assert compare_efficiency(baseline_not, candidate_first)[0]
    assert not compare_efficiency(baseline, TokenEfficiencyObservation(10, 6, 4, 1, 100, 50, 4, 1, 2, False))[0]
    assert compare_efficiency(baseline, accepted)[0]
    assert compare_efficiency(baseline, cheaper)[0]
    assert not compare_efficiency(baseline, input_growth)[0]
    assert not compare_efficiency(baseline, total_growth)[0]
    assert not compare_efficiency(baseline, low_cache, gate=EfficiencyGate(min_cache_hit_ratio=0.5))[0]
    assert compare_efficiency(baseline, extra_better_retention)[0]
    assert not compare_efficiency(baseline, extra_same_retention)[0]
    assert compare_efficiency(baseline, candidate_first)[0]
    assert not compare_efficiency(TokenEfficiencyObservation(1, 0, 1, 0, 0, 0, 0, accepted=True), baseline)[0]
    assert not compare_efficiency(TokenEfficiencyObservation(1, 1, 0, 0, 0, 0, 0, accepted=True), baseline)[0]


def test_run_record_validation_and_public_metadata():
    record = _record(
        evidence_selection=EvidenceSelectionMetrics(planned_context_units=4, retained_evidence_units=3, dropped_evidence_units=1, selected_evidence_count=1, source_count=1),
        token_efficiency=TokenEfficiencyMetrics(estimated_input_tokens=10, estimated_output_tokens=5, model_calls=2, cache_hits=1),
    )
    metadata = record.to_public_metadata()
    assert metadata["run_id"] == "run-1"
    assert metadata["token_efficiency"]["total_estimated_tokens"] == 15

    for field in ("planned_context_units", "retained_evidence_units", "dropped_evidence_units", "duplicate_evidence_dropped", "selected_evidence_count", "source_count"):
        values = {"planned_context_units": 4, "retained_evidence_units": 1, "dropped_evidence_units": 1, "duplicate_evidence_dropped": 1, "selected_evidence_count": 1, "source_count": 1}
        values[field] = -1
        with pytest.raises(ValueError):
            EvidenceSelectionMetrics(**values).validate()
    with pytest.raises(ValueError):
        EvidenceSelectionMetrics(planned_context_units=1, retained_evidence_units=1, dropped_evidence_units=1).validate()
    with pytest.raises(ValueError):
        EvidenceSelectionMetrics(selected_evidence_count=1, source_count=0).validate()

    for field in ("estimated_input_tokens", "estimated_output_tokens", "model_calls", "cache_hits", "deterministic_steps"):
        values = {"estimated_input_tokens": 1, "estimated_output_tokens": 1, "model_calls": 1, "cache_hits": 0, "deterministic_steps": 1}
        values[field] = -1
        with pytest.raises(ValueError):
            TokenEfficiencyMetrics(**values).validate()
    with pytest.raises(ValueError):
        TokenEfficiencyMetrics(cache_hits=2, model_calls=1).validate()
    with pytest.raises(ValueError):
        ResourceUsage(resource_units=-1).validate()
    with pytest.raises(ValueError):
        ResourceUsage(network_requests=-1).validate()
    with pytest.raises(ValueError):
        ResourceUsage(bytes=-1).validate()
    with pytest.raises(ValueError):
        ResourceUsage(ai_units=-1).validate()
    with pytest.raises(ValueError):
        ResourceUsage(wall_time_ms=-1).validate()
    with pytest.raises(ValueError):
        ResourceUsage(quota_state="").validate()
    with pytest.raises(ValueError):
        RunResult("bogus").validate()


def test_run_record_bounds_and_chain_guards():
    first = _receipt()
    base = _record()
    with pytest.raises(ValueError):
        _record(requested_fields=tuple("x" for _ in range(129))).validate()
    with pytest.raises(ValueError):
        _record(sources=tuple({} for _ in range(129))).validate()
    with pytest.raises(ValueError):
        _record(artifacts=tuple({} for _ in range(257)).validate()
    with pytest.raises(ValueError):
        _record(learning_note="x" * 1025).validate()
    broken = ChatbotRunRecord(**{**base.__dict__, "stages": ()})
    with pytest.raises(ValueError):
        broken.validate()
    broken_chain = ChatbotRunRecord(**{**base.__dict__, "stages": (first, _receipt("fetch", "wrong"))})
    with pytest.raises(ValueError):
        broken_chain.validate()
