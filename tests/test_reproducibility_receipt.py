import pytest

from benchmark.reproducibility import ensure_compatible, make_receipt, parse_receipt


def receipt(**changes):
    value = {
        "repository": "Z-Solo-King/foundation",
        "revision": "abc123",
        "artifact_id": "artifact-1",
        "suite": "nightly-project-improvement",
        "suite_version": "v1",
        "configuration": {"profile": "standard", "workers": 6},
        "evidence_tier": "deterministic_contract",
        "corpus_id": "project-research",
        "corpus_version": "v1",
        "execution_state": "completed",
        "workflow_id": "workflow-1",
        "workflow_run_id": "100",
        "generated_at": "2026-09-17T00:00:00Z",
    }
    value.update(changes)
    return make_receipt(**value)


def test_receipt_is_complete_and_round_trips():
    value = receipt()
    parsed = parse_receipt(value)
    assert parsed.repository == "Z-Solo-King/foundation"
    assert parsed.execution_state == "completed"
    assert len(parsed.configuration_digest) == 64


def test_sensitive_configuration_is_rejected():
    with pytest.raises(ValueError, match="sensitive field"):
        make_receipt(
            repository="repo",
            revision="rev",
            artifact_id="a",
            suite="suite",
            suite_version="v1",
            configuration={"api_key": "secret"},
            evidence_tier="deterministic_contract",
            corpus_id="c",
            corpus_version="v1",
            execution_state="completed",
        )


def test_incompatible_configuration_or_corpus_rejects_baseline():
    current = receipt()
    previous = receipt(configuration={"profile": "different", "workers": 6})
    compatible, reasons = ensure_compatible(current, previous)
    assert compatible is False
    assert any("configuration_digest" in reason for reason in reasons)

    current = receipt()
    previous = receipt(corpus_version="v2")
    compatible, reasons = ensure_compatible(current, previous)
    assert compatible is False
    assert any("corpus_version" in reason for reason in reasons)


def test_incomplete_previous_baseline_is_not_comparable():
    current = receipt(execution_state="partial")
    previous = receipt(execution_state="partial")
    compatible, reasons = ensure_compatible(current, previous)
    assert compatible is False
    assert "baseline comparison requires a completed previous execution state" in reasons
