import pytest

from backend.replay import ReplayBundle, ReplayCheckpoint, build_replay_bundle, digest_payload, replay_from_checkpoint


def test_replay_bundle_binds_inputs_and_resume_stage():
    bundle = build_replay_bundle(run_id="run-1", request_fingerprint="req-1", immutable_inputs={"question": "widget price", "budget": 5}, checkpoints=(ReplayCheckpoint("planned", digest_payload({"plan": 1}), 1), ReplayCheckpoint("acquired", digest_payload({"sources": ["a"]}), 2)))
    assert bundle.resume_stage == "acquired"
    assert replay_from_checkpoint(bundle, expected_inputs={"question": "widget price", "budget": 5}) == "acquired"
    assert bundle.to_dict()["schema"] == "research-replay-bundle/v1"


def test_empty_bundle_has_planned_resume_stage():
    bundle = build_replay_bundle(run_id="run-1", request_fingerprint="req-1", immutable_inputs={}, checkpoints=())
    assert bundle.resume_stage is None
    assert replay_from_checkpoint(bundle, expected_inputs={}) == "planned"


def test_checkpoint_validation_rejects_blank_digest_nonhex_and_nonpositive_sequence():
    with pytest.raises(ValueError, match="SHA-256 hex digest"):
        ReplayCheckpoint("planned", "", 1).validate()
    with pytest.raises(ValueError, match="hexadecimal"):
        ReplayCheckpoint("planned", "z" * 64, 1).validate()
    with pytest.raises(ValueError, match="positive"):
        ReplayCheckpoint("planned", "0" * 64, 0).validate()


def test_bundle_validation_rejects_blank_identity_and_invalid_input_digest():
    with pytest.raises(ValueError, match="run_id and request_fingerprint"):
        ReplayBundle("research-replay-bundle/v1", "", "req", (), "0" * 64, ()).validate()
    with pytest.raises(ValueError, match="run_id and request_fingerprint"):
        ReplayBundle("research-replay-bundle/v1", "run", "", (), "0" * 64, ()).validate()
    with pytest.raises(ValueError, match="immutable_inputs_digest"):
        ReplayBundle("research-replay-bundle/v1", "run", "req", (), "0", ()).validate()


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
    with pytest.raises(ValueError, match="artifact digests"):
        build_replay_bundle(run_id="run-1", request_fingerprint="req-1", immutable_inputs={}, checkpoints=(ReplayCheckpoint("planned", "0" * 64, 1),), artifact_digests=("z" * 64,))


def test_requested_resume_checkpoint_must_exist():
    bundle = build_replay_bundle(run_id="run-1", request_fingerprint="req-1", immutable_inputs={}, checkpoints=(ReplayCheckpoint("planned", "0" * 64, 1),))
    with pytest.raises(ValueError, match="not present"):
        replay_from_checkpoint(bundle, expected_inputs={}, last_completed_stage="verified")
    with pytest.raises(ValueError, match="unsupported completed stage"):
        replay_from_checkpoint(bundle, expected_inputs={}, last_completed_stage="unknown-stage")
