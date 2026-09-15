from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json


_SAFE_CHECKPOINTS = frozenset({"planned", "acquired", "extracted", "mapped", "verified", "published"})


@dataclass(frozen=True)
class ReplayCheckpoint:
    stage: str
    payload_digest: str
    sequence: int

    def validate(self) -> None:
        if self.stage not in _SAFE_CHECKPOINTS:
            raise ValueError("unsupported checkpoint stage")
        if not self.payload_digest or len(self.payload_digest) != 64:
            raise ValueError("payload_digest must be a SHA-256 hex digest")
        if any(char not in "0123456789abcdef" for char in self.payload_digest):
            raise ValueError("payload_digest must be hexadecimal")
        if self.sequence < 1:
            raise ValueError("sequence must be positive")


@dataclass(frozen=True)
class ReplayBundle:
    schema: str
    run_id: str
    request_fingerprint: str
    checkpoints: tuple[ReplayCheckpoint, ...]
    immutable_inputs_digest: str
    artifact_digests: tuple[str, ...]

    def validate(self) -> None:
        if self.schema != "research-replay-bundle/v1":
            raise ValueError("unsupported replay bundle schema")
        if not self.run_id.strip() or not self.request_fingerprint.strip():
            raise ValueError("run_id and request_fingerprint are required")
        if not self.immutable_inputs_digest or len(self.immutable_inputs_digest) != 64:
            raise ValueError("immutable_inputs_digest must be SHA-256")
        sequences = [checkpoint.sequence for checkpoint in self.checkpoints]
        if sequences != list(range(1, len(sequences) + 1)):
            raise ValueError("checkpoint sequences must be contiguous")
        for checkpoint in self.checkpoints:
            checkpoint.validate()
        if any(len(digest) != 64 or any(char not in "0123456789abcdef" for char in digest) for digest in self.artifact_digests):
            raise ValueError("artifact digests must be SHA-256 hex digests")

    @property
    def resume_stage(self) -> str | None:
        return self.checkpoints[-1].stage if self.checkpoints else None

    def to_dict(self) -> dict[str, object]:
        self.validate()
        return {
            "schema": self.schema,
            "run_id": self.run_id,
            "request_fingerprint": self.request_fingerprint,
            "checkpoints": [checkpoint.__dict__ for checkpoint in self.checkpoints],
            "immutable_inputs_digest": self.immutable_inputs_digest,
            "artifact_digests": list(self.artifact_digests),
        }


def digest_payload(payload: object) -> str:
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return sha256(encoded).hexdigest()


def build_replay_bundle(
    *,
    run_id: str,
    request_fingerprint: str,
    immutable_inputs: object,
    checkpoints: tuple[ReplayCheckpoint, ...],
    artifact_digests: tuple[str, ...] = (),
) -> ReplayBundle:
    bundle = ReplayBundle(
        schema="research-replay-bundle/v1",
        run_id=run_id,
        request_fingerprint=request_fingerprint,
        checkpoints=checkpoints,
        immutable_inputs_digest=digest_payload(immutable_inputs),
        artifact_digests=artifact_digests,
    )
    bundle.validate()
    return bundle


def replay_from_checkpoint(bundle: ReplayBundle, *, expected_inputs: object, last_completed_stage: str | None = None) -> str:
    bundle.validate()
    if bundle.immutable_inputs_digest != digest_payload(expected_inputs):
        raise ValueError("immutable replay inputs do not match bundle")
    if last_completed_stage is None:
        return bundle.resume_stage or "planned"
    if last_completed_stage not in _SAFE_CHECKPOINTS:
        raise ValueError("unsupported completed stage")
    completed = [checkpoint.stage for checkpoint in bundle.checkpoints]
    if last_completed_stage not in completed:
        raise ValueError("requested replay checkpoint is not present")
    return last_completed_stage
