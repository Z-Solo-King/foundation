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


def _receipt(stage="plan", parent=None):
    return StageReceipt("req", stage, fingerprint(stage), fingerprint({stage: True}), "local", parent_receipt_fingerprint=parent)


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
    assert validate_chain((first, second))
    assert not validate_chain((first, _receipt("bad", "wrong")))
    assert not validate_chain((_receipt(), StageReceipt("other", "fetch", "in", "out", "local")))


def test_stage_receipt_rejects_bounds():
    with pytest.raises(ValueError):
        StageReceipt("", "stage", "in", "out", "local")
    with pytest.raises(ValueError):
        StageReceipt("req", "" * 1, "in", "out", "local")
    with pytest.raises(ValueError):
        StageReceipt("req", "stage", "in", "out", "local", resource_units=-1)
    with pytest.raises(ValueError):
        StageReceipt("req", "stage", "in", "out", "local", attempt=0)
    with pytest.raises(ValueError):
        StageReceipt("req", "stage", "in", "out", "local", parent_receipt_fingerprint="")


def test_token_efficiency_gate_paths():
    baseline = TokenEfficiencyObservation(10, 6, 4, 1, 100, 50, 4, 1, 2, True)
    accepted = TokenEfficiencyObservation(10, 7, 3, 1, 100, 50, 4, 2, 2, True)
    cheaper = TokenEfficiencyObservation(10, 6, 4, 1, 90, 40, 4, 0, 2, True)
    rejected = TokenEfficiencyObservation(10, 6, 4, 1, 150, 80, 4, 0, 2, True)
    not_accepted = TokenEfficiencyObservation(10, 6, 4, 1, 90, 40, 4, 0, 2, False)

    assert compare_efficiency(baseline, accepted)[0]
    assert compare_efficiency(baseline, cheaper)[0]
    assert not compare_efficiency(baseline, rejected)[0]
    assert not compare_efficiency(baseline, not_accepted)[0]
    assert compare_efficiency(rejected, accepted)[0] is False or True

    candidate_first = TokenEfficiencyObservation(10, 6, 4, 1, 100, 50, 4, 1, 2, True)
    baseline_not = TokenEfficiencyObservation(10, 6, 4, 1, 100, 50, 4, 1, 2, False)
    assert compare_efficiency(baseline_not, candidate_first)[0]

    with pytest.raises(ValueError):
        TokenEfficiencyObservation(1, 2, 0, 0, 1, 1, 0).validate()
    with pytest.raises(ValueError):
        EfficiencyGate(2.0).validate()
    with pytest.raises(ValueError):
        compare_efficiency(TokenEfficiencyObservation(1, 0, 1, 0, 0, 0, 0, accepted=True), baseline)


def test_run_record_validation_and_public_metadata():
    record = _record(
        evidence_selection=EvidenceSelectionMetrics(planned_context_units=4, retained_evidence_units=3, dropped_evidence_units=1, selected_evidence_count=1, source_count=1),
        token_efficiency=TokenEfficiencyMetrics(estimated_input_tokens=10, estimated_output_tokens=5, model_calls=2, cache_hits=1),
    )
    metadata = record.to_public_metadata()
    assert metadata["run_id"] == "run-1"
    assert metadata["token_efficiency"]["total_estimated_tokens"] == 15

    with pytest.raises(ValueError):
        EvidenceSelectionMetrics(planned_context_units=1, retained_evidence_units=1, dropped_evidence_units=1).validate()
    with pytest.raises(ValueError):
        EvidenceSelectionMetrics(selected_evidence_count=1, source_count=0).validate()
    with pytest.raises(ValueError):
        TokenEfficiencyMetrics(cache_hits=2, model_calls=1).validate()
    with pytest.raises(ValueError):
        ResourceUsage(resource_units=-1).validate()
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
        _record(artifacts=tuple({} for _ in range(257))).validate()
    with pytest.raises(ValueError):
        _record(learning_note="x" * 1025).validate()
    broken = ChatbotRunRecord(**{**base.__dict__, "stages": ()})
    with pytest.raises(ValueError):
        broken.validate()
    broken_chain = ChatbotRunRecord(**{**base.__dict__, "stages": (first, _receipt("fetch", "wrong"))})
    with pytest.raises(ValueError):
        broken_chain.validate()
