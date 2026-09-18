from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
import hashlib
from typing import Iterable


ARTIFACT_CONTRACT_VERSION = "artifact/v1"


class ArtifactKind(StrEnum):
    DOCUMENT = "document"
    PDF = "pdf"
    HTML = "html"
    IMAGE = "image"
    SPREADSHEET = "spreadsheet"
    STRUCTURED_DATA = "structured_data"
    SOURCE_CODE = "source_code"
    PRESENTATION = "presentation"
    ARCHIVE = "archive"
    TEXT = "text"


class ArtifactSafety(StrEnum):
    PUBLIC = "public"
    PRIVATE = "private"
    UNTRUSTED = "untrusted"
    BLOCKED = "blocked"


class ArtifactValidation(StrEnum):
    UNVALIDATED = "unvalidated"
    VALID = "valid"
    PARTIAL = "partial"
    MALFORMED = "malformed"
    UNSUPPORTED = "unsupported"


class ExtractionMode(StrEnum):
    DETERMINISTIC = "deterministic"
    OCR = "ocr"
    MODEL_ASSISTED = "model_assisted"


SUPPORTED_ARTIFACT_KINDS = frozenset(ArtifactKind)


@dataclass(frozen=True)
class ArtifactPolicy:
    max_size_bytes: int = 50 * 1024 * 1024
    max_depth: int = 16
    allow_private_publication: bool = False

    def validate(self) -> None:
        if self.max_size_bytes < 1:
            raise ValueError("max_size_bytes must be positive")
        if self.max_depth < 1:
            raise ValueError("max_depth must be positive")


@dataclass(frozen=True)
class ArtifactRef:
    artifact_id: str
    kind: ArtifactKind
    media_type: str
    size_bytes: int
    content_fingerprint: str
    schema_fingerprint: str | None
    parser_version: str
    owner_scope: str
    provenance_parent: str | None
    safety: ArtifactSafety
    validation: ArtifactValidation
    retention_days: int | None = None
    publication_eligible: bool = False
    execution_identity: str | None = None

    def validate(self, policy: ArtifactPolicy = ArtifactPolicy()) -> None:
        policy.validate()
        if not self.artifact_id.strip() or not self.parser_version.strip() or not self.owner_scope.strip():
            raise ValueError("artifact identity, parser version and owner scope are required")
        if self.kind not in SUPPORTED_ARTIFACT_KINDS:
            raise ValueError("unsupported artifact kind")
        if not self.media_type.strip():
            raise ValueError("media_type is required")
        if self.size_bytes < 0 or self.size_bytes > policy.max_size_bytes:
            raise ValueError("artifact size exceeds policy")
        if len(self.content_fingerprint) != 64 or any(ch not in "0123456789abcdef" for ch in self.content_fingerprint.lower()):
            raise ValueError("content_fingerprint must be SHA-256")
        if self.schema_fingerprint is not None and (
            len(self.schema_fingerprint) != 64
            or any(ch not in "0123456789abcdef" for ch in self.schema_fingerprint.lower())
        ):
            raise ValueError("schema_fingerprint must be SHA-256")
        if self.retention_days is not None and self.retention_days < 0:
            raise ValueError("retention_days must be non-negative")
        if self.safety is ArtifactSafety.PRIVATE and self.publication_eligible and not policy.allow_private_publication:
            raise ValueError("private artifacts cannot be public-published by default")
        if self.validation in {ArtifactValidation.MALFORMED, ArtifactValidation.UNSUPPORTED} and self.publication_eligible:
            raise ValueError("malformed or unsupported artifacts cannot be published")
        if self.safety is ArtifactSafety.BLOCKED and self.publication_eligible:
            raise ValueError("blocked artifacts cannot be published")


def content_fingerprint(content: bytes | bytearray | memoryview | str) -> str:
    payload = content.encode("utf-8") if isinstance(content, str) else bytes(content)
    return hashlib.sha256(payload).hexdigest()


def deterministic_artifact_id(parent: str | None, content_hash: str, parser_version: str) -> str:
    if not content_hash or not parser_version.strip():
        raise ValueError("artifact identity inputs are required")
    seed = f"{parent or 'root'}:{content_hash}:{parser_version}".encode("utf-8")
    return "artifact-" + hashlib.sha256(seed).hexdigest()[:24]


def create_artifact(
    content: bytes | str,
    *,
    kind: ArtifactKind,
    media_type: str,
    parser_version: str,
    owner_scope: str,
    parent_artifact: str | None = None,
    schema_fingerprint: str | None = None,
    safety: ArtifactSafety = ArtifactSafety.UNTRUSTED,
    validation: ArtifactValidation = ArtifactValidation.UNVALIDATED,
    retention_days: int | None = None,
    publication_eligible: bool = False,
    execution_identity: str | None = None,
    policy: ArtifactPolicy = ArtifactPolicy(),
) -> ArtifactRef:
    digest = content_fingerprint(content)
    artifact = ArtifactRef(
        artifact_id=deterministic_artifact_id(parent_artifact, digest, parser_version),
        kind=kind,
        media_type=media_type,
        size_bytes=len(content.encode("utf-8")) if isinstance(content, str) else len(content),
        content_fingerprint=digest,
        schema_fingerprint=schema_fingerprint,
        parser_version=parser_version,
        owner_scope=owner_scope,
        provenance_parent=parent_artifact,
        safety=safety,
        validation=validation,
        retention_days=retention_days,
        publication_eligible=publication_eligible,
        execution_identity=execution_identity,
    )
    artifact.validate(policy)
    return artifact


@dataclass(frozen=True)
class AdapterContract:
    kind: ArtifactKind
    accepted_media_types: tuple[str, ...]
    extraction_version: str
    extraction_mode: ExtractionMode = ExtractionMode.DETERMINISTIC
    max_input_bytes: int = 50 * 1024 * 1024
    output_schema_version: str = "artifact-adapter/v1"

    def validate(self) -> None:
        if self.kind not in SUPPORTED_ARTIFACT_KINDS:
            raise ValueError("unsupported adapter kind")
        if not self.accepted_media_types or any(not item.strip() for item in self.accepted_media_types):
            raise ValueError("accepted_media_types must not be empty")
        if not self.extraction_version.strip() or not self.output_schema_version.strip():
            raise ValueError("adapter versions are required")
        if self.max_input_bytes < 1:
            raise ValueError("max_input_bytes must be positive")


@dataclass(frozen=True)
class AdapterResult:
    schema_version: str
    input_fingerprint: str
    output_fingerprint: str | None
    extraction_mode: ExtractionMode
    warnings: tuple[str, ...] = ()
    unsupported_features: tuple[str, ...] = ()
    stable_region_ids: tuple[str, ...] = ()

    def validate(self) -> None:
        if not self.schema_version.strip():
            raise ValueError("adapter result schema_version is required")
        for value in (self.input_fingerprint,):
            if len(value) != 64:
                raise ValueError("adapter fingerprints must be SHA-256")
        if self.output_fingerprint is not None and len(self.output_fingerprint) != 64:
            raise ValueError("adapter output fingerprint must be SHA-256")
        if any(not item.strip() for item in self.warnings + self.unsupported_features + self.stable_region_ids):
            raise ValueError("adapter metadata values must not be empty")


class ArtifactExecutionState(StrEnum):
    AUTHORIZED = "authorized"
    BLOCKED = "blocked"
    REQUIRES_AUTHORIZATION = "requires_authorization"


@dataclass(frozen=True)
class ArtifactExecutionDecision:
    state: ArtifactExecutionState
    reason: str
    artifact_id: str
    target_scope: str

    def to_dict(self) -> dict[str, str]:
        return {
            "schema_version": "artifact-execution/v1",
            "state": self.state.value,
            "reason": self.reason,
            "artifact_id": self.artifact_id,
            "target_scope": self.target_scope,
        }


def authorize_artifact_execution(
    artifact: ArtifactRef,
    *,
    target_scope: str,
    explicit_authorization: bool = False,
) -> ArtifactExecutionDecision:
    if not target_scope.strip():
        raise ValueError("target_scope is required")
    if artifact.safety is ArtifactSafety.BLOCKED:
        return ArtifactExecutionDecision(
            ArtifactExecutionState.BLOCKED,
            "blocked artifacts cannot enter execution",
            artifact.artifact_id,
            target_scope,
        )
    if artifact.validation in {ArtifactValidation.MALFORMED, ArtifactValidation.UNSUPPORTED}:
        return ArtifactExecutionDecision(
            ArtifactExecutionState.BLOCKED,
            "invalid or unsupported artifacts cannot enter execution",
            artifact.artifact_id,
            target_scope,
        )
    private_cross_scope = artifact.safety is ArtifactSafety.PRIVATE and target_scope != artifact.owner_scope
    if private_cross_scope and not explicit_authorization:
        return ArtifactExecutionDecision(
            ArtifactExecutionState.REQUIRES_AUTHORIZATION,
            "private artifact cannot cross scope without explicit authorization",
            artifact.artifact_id,
            target_scope,
        )
    return ArtifactExecutionDecision(
        ArtifactExecutionState.AUTHORIZED,
        "artifact execution boundary satisfied",
        artifact.artifact_id,
        target_scope,
    )


def derive_artifact(
    parent: ArtifactRef,
    content: bytes | str,
    *,
    kind: ArtifactKind,
    media_type: str,
    parser_version: str,
    validation: ArtifactValidation = ArtifactValidation.UNVALIDATED,
    safety: ArtifactSafety | None = None,
    retention_days: int | None = None,
    publication_eligible: bool = False,
    policy: ArtifactPolicy = ArtifactPolicy(),
) -> ArtifactRef:
    """Create a derived artifact while preserving explicit parent lineage."""
    return create_artifact(
        content,
        kind=kind,
        media_type=media_type,
        parser_version=parser_version,
        owner_scope=parent.owner_scope,
        parent_artifact=parent.artifact_id,
        safety=safety or parent.safety,
        validation=validation,
        retention_days=retention_days,
        publication_eligible=publication_eligible,
        execution_identity=parent.execution_identity,
        policy=policy,
    )
