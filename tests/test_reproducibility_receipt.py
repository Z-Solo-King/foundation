import pytest

from backend.reproducibility_receipt import build_receipt, compatible_baseline


def receipt(**overrides):
    values = dict(schema="reproducibility-receipt/v1", repository="foundation", revision="abc123", workflow_run_id="run-1", suite_version="suite-1", configuration="full", model_provider_mode="contract", evidence_tier="L3", fixture_id="fixture-1", fixture_version="1", execution_state="COMPLETE", executed_at="2026-09-17T00:00:00Z", runtime_class="github-actions")
    values.update(overrides)
    return build_receipt(**values)


def test_receipt_is_deterministic_and_self_validating():
    first, second = receipt(), receipt()
    assert first.artifact_digest == second.artifact_digest
    first.validate()


def test_tampering_is_rejected():
    value = receipt()
    object.__setattr__(value, "revision", "tampered")
    with pytest.raises(ValueError, match="digest"):
        value.validate()


def test_incompatible_baseline_is_rejected():
    assert compatible_baseline(receipt(), receipt())
    assert not compatible_baseline(receipt(suite_version="suite-2"), receipt())


def test_production_cannot_hide_non_execution():
    with pytest.raises(ValueError, match="production"):
        receipt(evidence_tier="PRODUCTION", execution_state="UNKNOWN")
