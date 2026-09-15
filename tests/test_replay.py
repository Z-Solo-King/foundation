import pytest

from backend.replay import ReplayCheckpoint, build_replay_bundle, digest_payload, replay_from_checkpoint


def test_replay_bundle_binds_inputs_and_resume_stage():
    bundle = build_replay_bundle(run_id="run-1", request_fingerprint="req-1", immutable_inputs={"question": "widget price", "budget": 5}, checkpoints=(ReplayCheckpoint("planned", digest_payload({"plan": 1}), 1), ReplayCheckpoint("acquired", digest_payload({"sources": ["a"]}), 2)))
    assert bundle.resume_stage == "acquired"
    assert replay_from_checkpoint(bundle, expected_inputs={"question": "widget price", "budget": 5}) == "acquired"


def test_input_mismatch_fails_closed():
    bundle = build_replay_bundle(run_id="run-1", request_fingerprint="req-1", immutable_inputs={"question": "widget price"}, checkpoints=(ReplayCheckpoint("planned", digest_payload({"plan": 1}), 1),))
    with pytest.raises(ValueError, match="immutable replay inputs"):
        replay_from_checkpoint(bundle, expected_inputs={"question": "other"})


def test_unknown_checkpoint_stage_rejected():
    with pytest.raises(ValueError):
        ReplayCheckpoint("not-safe", "0" * 64, 1).validate()


def test_duplicate_or_gapped_checkpoint_sequences_rejected():
    with pytest.raises(ValueError, match="contiguous"):
        build_replay_bundle(run_id="run-1", request_fingerprint="req-1", immutable_inputs={}, checkpoints=(ReplayCheckpoint("planned", "0" * 64, 1), ReplayCheckpoint("acquired", "1" * 64, 3)))


def test_corrupt_artifact_digest_rejected():
    with pytest.raises(ValueError, match="artifact digests"):
        build_replay_bundle(run_id="run-1", request_fingerprint="req-1", immutable_inputs={}, checkpoints=(ReplayCheckpoint("planned", "0" * 64, 1),), artifact_digests=("not-a-digest",))


def test_requested_resume_checkpoint_must_exist():
    bundle = build_replay_bundle(run_id="run-1", request_fingerprint="req-1", immutable_inputs={}, checkpoints=(ReplayCheckpoint("planned", "0" * 64, 1),))
    with pytest.raises(ValueError, match="not present"):
        replay_from_checkpoint(bundle, expected_inputs={}, last_completed_stage="verified")
