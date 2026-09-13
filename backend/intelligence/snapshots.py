from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
import json


@dataclass(frozen=True)
class DocumentVersion:
    version_id: str
    document_id: str
    content_hash: str
    observed_at: datetime
    parent_version_id: str | None = None
    extractor_version: str | None = None
    mapper_version: str | None = None
    retention_state: str | None = None

    def validate(self) -> None:
        for name in ("version_id", "document_id", "content_hash"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must not be empty")
        if len(self.content_hash) != 64:
            raise ValueError("content_hash must be a SHA-256 hex digest")
        for name in ("parent_version_id", "extractor_version", "mapper_version", "retention_state"):
            value = getattr(self, name)
            if value is not None and (not isinstance(value, str) or len(value) > 4096):
                raise ValueError(f"{name} exceeds bounded length")

    def fingerprint(self) -> str:
        self.validate()
        payload = {
            "version_id": self.version_id,
            "document_id": self.document_id,
            "content_hash": self.content_hash,
            "observed_at": self.observed_at.isoformat(),
            "parent_version_id": self.parent_version_id,
            "extractor_version": self.extractor_version,
            "mapper_version": self.mapper_version,
            "retention_state": self.retention_state,
        }
        return sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


@dataclass(frozen=True)
class ClaimSnapshot:
    snapshot_id: str
    claim_id: str
    text: str
    observed_at: datetime
    document_version_id: str | None = None
    evidence_fingerprint: str | None = None
    revision_number: int = 1
    parent_snapshot_id: str | None = None

    @classmethod
    def create(cls, snapshot_id, claim_id, text, *, document_version_id=None, evidence_fingerprint=None, revision_number=1, parent_snapshot_id=None):
        snapshot = cls(snapshot_id, claim_id, text, datetime.now(timezone.utc), document_version_id, evidence_fingerprint, revision_number, parent_snapshot_id)
        snapshot.validate()
        return snapshot

    def validate(self) -> None:
        for name in ("snapshot_id", "claim_id", "text"):
            if not isinstance(getattr(self, name), str) or not getattr(self, name).strip():
                raise ValueError(f"{name} must not be empty")
        if self.revision_number < 1:
            raise ValueError("revision_number must be positive")
        for name in ("document_version_id", "evidence_fingerprint", "parent_snapshot_id"):
            value = getattr(self, name)
            if value is not None and (not isinstance(value, str) or len(value) > 4096):
                raise ValueError(f"{name} exceeds bounded length")


def changed(previous: ClaimSnapshot, current: ClaimSnapshot) -> bool:
    return previous.claim_id == current.claim_id and previous.text != current.text