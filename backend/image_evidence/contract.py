from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
import hashlib


IMAGE_EVIDENCE_CONTRACT_VERSION = "image-evidence/v1"


class ImageEvidenceMode(StrEnum):
    OCR = "ocr"
    VISUAL_ATTRIBUTE = "visual_attribute"
    SPECIFICATION = "specification"
    FAMILY_HINT = "family_hint"
    PERCEPTUAL_FINGERPRINT = "perceptual_fingerprint"


class ImageEvidenceStatus(StrEnum):
    OBSERVED = "observed"
    UNKNOWN = "unknown"
    UNREADABLE = "unreadable"
    BLOCKED = "blocked"


@dataclass(frozen=True)
class ImageRegion:
    region_id: str
    x: float
    y: float
    width: float
    height: float

    def validate(self) -> None:
        if not self.region_id.strip():
            raise ValueError("region_id is required")
        values = (self.x, self.y, self.width, self.height)
        if any(value < 0 for value in values):
            raise ValueError("region geometry must be non-negative")
        if self.width == 0 or self.height == 0:
            raise ValueError("region width and height must be positive")


@dataclass(frozen=True)
class ImageObservation:
    observation_id: str
    mode: ImageEvidenceMode
    status: ImageEvidenceStatus
    value: str | None
    confidence_milli: int | None
    region: ImageRegion | None
    image_fingerprint: str
    model_version: str | None = None

    def validate(self) -> None:
        if not self.observation_id.strip():
            raise ValueError("observation_id is required")
        if len(self.image_fingerprint) != 64 or any(ch not in "0123456789abcdef" for ch in self.image_fingerprint.lower()):
            raise ValueError("image_fingerprint must be SHA-256")
        if self.confidence_milli is not None and not 0 <= self.confidence_milli <= 1_000:
            raise ValueError("confidence_milli must be between 0 and 1000")
        if self.status is ImageEvidenceStatus.OBSERVED and not (self.value or "").strip():
            raise ValueError("observed image evidence requires a value")
        if self.status is not ImageEvidenceStatus.OBSERVED and self.value is not None:
            raise ValueError("non-observed image evidence cannot carry an observed value")
        if self.region is not None:
            self.region.validate()


@dataclass(frozen=True)
class ImageEvidenceRequest:
    image_fingerprint: str
    max_bytes: int = 10 * 1024 * 1024
    max_observations: int = 32
    allowed_modes: tuple[ImageEvidenceMode, ...] = (
        ImageEvidenceMode.OCR,
        ImageEvidenceMode.SPECIFICATION,
        ImageEvidenceMode.PERCEPTUAL_FINGERPRINT,
    )

    def validate(self) -> None:
        if len(self.image_fingerprint) != 64:
            raise ValueError("image_fingerprint must be SHA-256")
        if self.max_bytes < 1 or self.max_observations < 1:
            raise ValueError("image evidence limits must be positive")
        if not self.allowed_modes:
            raise ValueError("at least one image evidence mode is required")


@dataclass(frozen=True)
class ImageEvidenceResult:
    schema_version: str
    image_fingerprint: str
    observations: tuple[ImageObservation, ...]
    derived: bool = True
    execution_identity: str | None = None

    def validate(self) -> None:
        if self.schema_version != IMAGE_EVIDENCE_CONTRACT_VERSION:
            raise ValueError("unsupported image evidence contract version")
        if not self.derived:
            raise ValueError("image observations must remain derived evidence")
        if len(self.image_fingerprint) != 64:
            raise ValueError("image_fingerprint must be SHA-256")
        for observation in self.observations:
            if observation.image_fingerprint != self.image_fingerprint:
                raise ValueError("observation fingerprint does not match source image")
            observation.validate()


def image_content_fingerprint(content: bytes | str) -> str:
    payload = content.encode("utf-8") if isinstance(content, str) else bytes(content)
    return hashlib.sha256(payload).hexdigest()


def select_image_modes(request: ImageEvidenceRequest, *, budget_units: int) -> tuple[ImageEvidenceMode, ...]:
    request.validate()
    if budget_units < 1:
        return ()
    ordered = (
        ImageEvidenceMode.OCR,
        ImageEvidenceMode.SPECIFICATION,
        ImageEvidenceMode.VISUAL_ATTRIBUTE,
        ImageEvidenceMode.FAMILY_HINT,
        ImageEvidenceMode.PERCEPTUAL_FINGERPRINT,
    )
    selected = tuple(mode for mode in ordered if mode in request.allowed_modes)
    return selected[: min(len(selected), budget_units, request.max_observations)]
