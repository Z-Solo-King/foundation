import pytest

from backend.result_envelope import (
    FreshnessState,
    ResultEnvelope,
    ResultStatus,
    envelope_from_legacy_response,
)


def test_completed_envelope_serializes_stable_public_shape():
    envelope = ResultEnvelope(
        status=ResultStatus.COMPLETED,
        result={"answer": "ok"},
        requested_scope=("q1",),
        completed_scope=("q1",),
        claim_support={"c1": "SUPPORTED"},
        freshness=FreshnessState.FRESH,
        provenance_refs=("evidence:1",),
        execution_identity="exec-1",
    )
    payload = envelope.to_dict()
    assert payload["schema_version"] == "heroic-ai-result/v1"
    assert payload["status"] == "COMPLETED"
    assert payload["scope"]["completed"] == ["q1"]
    assert payload["freshness"] == "FRESH"


@pytest.mark.parametrize("status", [
    ResultStatus.PARTIAL,
    ResultStatus.DEGRADED,
    ResultStatus.BLOCKED,
    ResultStatus.FAILED,
    ResultStatus.CANCELLED,
])
def test_non_completed_states_are_explicit(status):
    envelope = ResultEnvelope(
        status=status,
        result={"answer": "qualified"},
        missing_scope=("q2",) if status is ResultStatus.PARTIAL else (),
        warnings=("qualified",),
    )
    assert envelope.to_dict()["status"] == status.value


def test_completed_rejects_missing_failed_unresolved_and_stale_state():
    with pytest.raises(ValueError, match="missing or failed"):
        ResultEnvelope(
            status=ResultStatus.COMPLETED,
            missing_scope=("q2",),
        ).to_dict()

    with pytest.raises(ValueError, match="missing or failed"):
        ResultEnvelope(
            status=ResultStatus.COMPLETED,
            failed_scope=("q2",),
        ).to_dict()

    with pytest.raises(ValueError, match="unresolved"):
        ResultEnvelope(
            status=ResultStatus.COMPLETED,
            claim_support={"c1": "UNKNOWN"},
        ).to_dict()

    with pytest.raises(ValueError, match="stale"):
        ResultEnvelope(
            status=ResultStatus.COMPLETED,
            freshness=FreshnessState.STALE,
        ).to_dict()


def test_schema_version_and_identity_validation_fail_closed():
    with pytest.raises(ValueError, match="schema"):
        ResultEnvelope(schema_version="heroic-ai-result/v2").to_dict()
    with pytest.raises(ValueError, match="execution_identity"):
        ResultEnvelope(execution_identity="   ").to_dict()


def test_legacy_adapter_preserves_metadata_and_run_identity():
    envelope = envelope_from_legacy_response(
        ok=True,
        run_id="run-1",
        metadata={"question": "test"},
    )
    payload = envelope.to_dict()
    assert payload["result"]["run_id"] == "run-1"
    assert payload["result"]["question"] == "test"


def test_legacy_adapter_prefers_explicit_result_payload():
    envelope = envelope_from_legacy_response(
        ok=True,
        result={"answer": "ok"},
        run_id="run-2",
        metadata={"ignored": True},
    )
    assert envelope.to_dict()["result"] == {"answer": "ok"}


def test_legacy_error_adapter_is_explicitly_failed():
    envelope = envelope_from_legacy_response(ok=False, error="blocked")
    payload = envelope.to_dict()
    assert payload["status"] == "FAILED"
    assert payload["warnings"] == ["blocked"]


def test_legacy_error_adapter_allows_missing_error_without_false_detail():
    envelope = envelope_from_legacy_response(ok=False)
    payload = envelope.to_dict()
    assert payload["status"] == "FAILED"
    assert payload["warnings"] == []
