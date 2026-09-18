import pytest

from backend.publication_gate import (
    PublicationGateSnapshot,
    PublicationOutcome,
    decide_publication,
)


def valid_snapshot(**changes):
    payload = dict(
        execution_state="completed",
        claim_states=("SUPPORTED",),
        freshness_state="fresh",
        evidence_integrity=True,
        independent_evidence=True,
        policy_eligible=True,
        provenance_complete=True,
        private_evidence=False,
    )
    payload.update(changes)
    return PublicationGateSnapshot(**payload)


def test_publication_gate_publishes_only_when_all_gates_pass():
    decision = decide_publication(valid_snapshot())
    assert decision.outcome is PublicationOutcome.PUBLISH_COMPLETED
    assert len(decision.fingerprint) == 64


def test_private_policy_and_execution_failures_block_or_withhold():
    assert decide_publication(valid_snapshot(private_evidence=True)).outcome is PublicationOutcome.BLOCK_PRIVATE_EVIDENCE
    assert decide_publication(valid_snapshot(policy_eligible=False)).outcome is PublicationOutcome.BLOCK_POLICY
    assert decide_publication(valid_snapshot(execution_state="failed")).outcome is PublicationOutcome.WITHHOLD_EXECUTION
    assert decide_publication(valid_snapshot(execution_state="blocked")).outcome is PublicationOutcome.WITHHOLD_EXECUTION
    assert decide_publication(valid_snapshot(execution_state="cancelled")).outcome is PublicationOutcome.WITHHOLD_EXECUTION


def test_evidence_freshness_claim_and_provenance_failures_are_distinct():
    assert decide_publication(valid_snapshot(evidence_integrity=False)).outcome is PublicationOutcome.WITHHOLD_EVIDENCE
    assert decide_publication(valid_snapshot(independent_evidence=False)).outcome is PublicationOutcome.WITHHOLD_EVIDENCE
    assert decide_publication(valid_snapshot(freshness_state="stale")).outcome is PublicationOutcome.WITHHOLD_FRESHNESS
    assert decide_publication(valid_snapshot(freshness_state="unknown")).outcome is PublicationOutcome.WITHHOLD_FRESHNESS
    assert decide_publication(valid_snapshot(claim_states=("SUPPORTED", "UNKNOWN"))).outcome is PublicationOutcome.WITHHOLD_CLAIMS
    assert decide_publication(valid_snapshot(provenance_complete=False)).outcome is PublicationOutcome.WITHHOLD_PROVENANCE


def test_partial_publication_is_explicit_and_deterministic():
    missing = decide_publication(valid_snapshot(missing_scope=1))
    failed = decide_publication(valid_snapshot(failed_scope=1))
    partial = decide_publication(valid_snapshot(execution_state="partial"))
    assert missing.outcome is PublicationOutcome.PUBLISH_PARTIAL
    assert failed.outcome is PublicationOutcome.PUBLISH_PARTIAL
    assert partial.outcome is PublicationOutcome.PUBLISH_PARTIAL
    assert missing.fingerprint != failed.fingerprint


def test_snapshot_validation_is_fail_closed():
    with pytest.raises(ValueError):
        PublicationGateSnapshot(execution_state="running").validate()
    with pytest.raises(ValueError):
        PublicationGateSnapshot(execution_state="completed", missing_scope=-1).validate()
    with pytest.raises(ValueError):
        PublicationGateSnapshot(execution_state="completed", freshness_state="bad").validate()
    with pytest.raises(ValueError):
        PublicationGateSnapshot(execution_state="completed", claim_states=("",)).validate()


def test_identical_gate_snapshots_have_stable_decisions():
    snapshot = valid_snapshot()
    first = decide_publication(snapshot)
    second = decide_publication(snapshot)
    assert first == second
