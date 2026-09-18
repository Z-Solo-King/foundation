from datetime import datetime, timezone

import pytest

from backend.intelligence.snapshots import AnswerSnapshot, ClaimSnapshot, changed


def claim(snapshot_id, claim_id, text):
    return ClaimSnapshot(snapshot_id, claim_id, text, datetime.now(timezone.utc))


def answer(result="digest-a", latency=100, resources=10):
    return AnswerSnapshot(
        snapshot_id="s1",
        execution_identity="exec-1",
        requested_scope=("q1",),
        completed_scope=("q1",),
        claim_support={"c1": "SUPPORTED"},
        freshness={"c1": "FRESH"},
        source_fingerprints=("source-a",),
        capability_version="cap-v1",
        policy_version="policy-v1",
        result_digest=result,
        resource_units=resources,
        latency_ms=latency,
    )


def test_claim_snapshot_legacy_behavior_remains():
    previous = claim("s1", "c1", "old")
    current = claim("s2", "c1", "new")
    assert changed(previous, current) is True
    assert changed(previous, previous) is False


def test_answer_snapshot_semantic_diff_is_stable():
    previous = answer()
    current = answer(result="digest-b", latency=120, resources=12)
    diff = previous.semantic_diff(current)
    assert diff["result_changed"] is True
    assert diff["latency_changed"] is True
    assert diff["resource_changed"] is True
    assert diff["claim_support_changed"] is False


def test_answer_snapshot_ignores_presentation_only_changes():
    previous = answer()
    current = AnswerSnapshot(
        **{**previous.__dict__, "snapshot_id": "s2"}
    )
    assert not any(previous.semantic_diff(current).values())


def test_answer_snapshot_detects_policy_and_evidence_changes():
    previous = answer()
    current = AnswerSnapshot(
        **{
            **previous.__dict__,
            "claim_support": {"c1": "QUALIFIED"},
            "freshness": {"c1": "STALE"},
            "source_fingerprints": ("source-b",),
            "policy_version": "policy-v2",
        }
    )
    diff = previous.semantic_diff(current)
    assert diff["claim_support_changed"]
    assert diff["freshness_changed"]
    assert diff["sources_changed"]
    assert diff["policy_changed"]


def test_answer_snapshot_validation_rejects_missing_identity_or_negative_metrics():
    with pytest.raises(ValueError):
        AnswerSnapshot("", "e", (), (), {}, {}, (), "c", "p", "d").validate()
    with pytest.raises(ValueError):
        AnswerSnapshot("s", "e", (), (), {}, {}, (), "c", "p", "d", resource_units=-1).validate()


def test_answer_snapshot_validation_rejects_missing_capability_policy_and_digest():
    with pytest.raises(ValueError):
        AnswerSnapshot("s", "e", (), (), {}, {}, (), "", "p", "d").validate()
    with pytest.raises(ValueError):
        AnswerSnapshot("s", "e", (), (), {}, {}, (), "c", "", "d").validate()
    with pytest.raises(ValueError):
        AnswerSnapshot("s", "e", (), (), {}, {}, (), "c", "p", "").validate()
