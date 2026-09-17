from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone

SCHEMA = "benchmark-reproducibility/v1"
_FORBIDDEN_KEY_PARTS = ("password", "secret", "token", "private_key", "api_key", "authorization", "prompt")
_ALLOWED_EXECUTION_STATES = {"completed", "partial_or_failed"}


@dataclass(frozen=True)
class ReproducibilityReceipt:
    repository: str
    revision: str
    artifact_id: str
    suite: str
    suite_version: str
    configuration_digest: str
    evidence_tier: str
    corpus_id: str
    corpus_version: str
    execution_state: str
    generated_at: str
    workflow_id: str | None = None
    workflow_run_id: str | None = None

    def to_dict(self) -> dict[str, object]:
        return {
            "schema": SCHEMA,
            "repository": self.repository,
            "revision": self.revision,
            "artifact_id": self.artifact_id,
            "suite": self.suite,
            "suite_version": self.suite_version,
            "configuration_digest": self.configuration_digest,
            "evidence_tier": self.evidence_tier,
            "corpus_id": self.corpus_id,
            "corpus_version": self.corpus_version,
            "execution_state": self.execution_state,
            "generated_at": self.generated_at,
            "workflow_id": self.workflow_id,
            "workflow_run_id": self.workflow_run_id,
        }

    def validate(self) -> None:
        values = (
            self.repository,
            self.revision,
            self.artifact_id,
            self.suite,
            self.suite_version,
            self.configuration_digest,
            self.evidence_tier,
            self.corpus_id,
            self.corpus_version,
            self.execution_state,
            self.generated_at,
        )
        if any(not isinstance(value, str) or not value.strip() for value in values):
            raise ValueError("reproducibility receipt contains missing required metadata")
        if self.workflow_id is not None and not self.workflow_id.strip():
            raise ValueError("workflow_id cannot be blank")
        if self.workflow_run_id is not None and not self.workflow_run_id.strip():
            raise ValueError("workflow_run_id cannot be blank")


def canonical_configuration_digest(configuration: object) -> str:
    _reject_sensitive(configuration)
    payload = json.dumps(configuration, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _reject_sensitive(value: object, path: str = "root") -> None:
    if isinstance(value, dict):
        for key, nested in value.items():
            normalized = str(key).lower().replace("-", "_")
            if any(part in normalized for part in _FORBIDDEN_KEY_PARTS):
                raise ValueError(f"sensitive field is not permitted in reproducibility metadata: {path}.{key}")
            _reject_sensitive(nested, f"{path}.{key}")
    elif isinstance(value, (list, tuple)):
        for index, nested in enumerate(value):
            _reject_sensitive(nested, f"{path}[{index}]")


def parse_receipt(value: object) -> ReproducibilityReceipt:
    if not isinstance(value, dict) or value.get("schema") != SCHEMA:
        raise ValueError("unsupported or missing reproducibility receipt schema")
    receipt = ReproducibilityReceipt(
        repository=str(value.get("repository", "")),
        revision=str(value.get("revision", "")),
        artifact_id=str(value.get("artifact_id", "")),
        suite=str(value.get("suite", "")),
        suite_version=str(value.get("suite_version", "")),
        configuration_digest=str(value.get("configuration_digest", "")),
        evidence_tier=str(value.get("evidence_tier", "")),
        corpus_id=str(value.get("corpus_id", "")),
        corpus_version=str(value.get("corpus_version", "")),
        execution_state=str(value.get("execution_state", "")),
        generated_at=str(value.get("generated_at", "")),
        workflow_id=None if value.get("workflow_id") is None else str(value.get("workflow_id")),
        workflow_run_id=None if value.get("workflow_run_id") is None else str(value.get("workflow_run_id")),
    )
    receipt.validate()
    return receipt


def ensure_compatible(current: object, previous: object) -> tuple[bool, list[str]]:
    """Check whether two artifacts share a reproducible comparison identity.

    A completed run can be compared with either a completed or valid partial
    prior run. This permits truthful recovery comparisons while still rejecting
    missing/unknown execution state.
    """
    current_receipt = parse_receipt(current)
    previous_receipt = parse_receipt(previous)
    errors: list[str] = []
    for field in (
        "repository",
        "suite",
        "suite_version",
        "configuration_digest",
        "evidence_tier",
        "corpus_id",
        "corpus_version",
    ):
        left = getattr(current_receipt, field)
        right = getattr(previous_receipt, field)
        if left != right:
            errors.append(f"incompatible {field}: current={left!r} previous={right!r}")
    if current_receipt.execution_state not in _ALLOWED_EXECUTION_STATES:
        errors.append(f"unsupported current execution state: {current_receipt.execution_state!r}")
    if previous_receipt.execution_state not in _ALLOWED_EXECUTION_STATES:
        errors.append(f"unsupported previous execution state: {previous_receipt.execution_state!r}")
    return not errors, errors


def make_receipt(
    *,
    repository: str,
    revision: str,
    artifact_id: str,
    suite: str,
    suite_version: str,
    configuration: object,
    evidence_tier: str,
    corpus_id: str,
    corpus_version: str,
    execution_state: str,
    workflow_id: str | None = None,
    workflow_run_id: str | None = None,
    generated_at: str | None = None,
) -> dict[str, object]:
    receipt = ReproducibilityReceipt(
        repository=repository,
        revision=revision,
        artifact_id=artifact_id,
        suite=suite,
        suite_version=suite_version,
        configuration_digest=canonical_configuration_digest(configuration),
        evidence_tier=evidence_tier,
        corpus_id=corpus_id,
        corpus_version=corpus_version,
        execution_state=execution_state,
        generated_at=generated_at or datetime.now(timezone.utc).isoformat(),
        workflow_id=workflow_id,
        workflow_run_id=workflow_run_id,
    )
    receipt.validate()
    return receipt.to_dict()
