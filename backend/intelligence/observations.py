from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from hashlib import sha256
import json
from typing import Any


@dataclass(frozen=True, init=False)
class Observation:
    """Canonical provenance-preserving observation record.

    Older positional construction remains supported. New code should prefer
    keyword construction so richer provenance fields remain explicit.
    """

    observation_id: str
    source_url: str
    content: str
    observed_at: datetime
    source_id: str | None = None
    source_family_id: str | None = None
    document_version_id: str | None = None
    retrieved_at: datetime | None = None
    published_at: datetime | None = None
    author: str | None = None
    language: str | None = None
    title: str | None = None
    structured_data: Any = None
    evidence_spans: tuple[Any, ...] = ()
    extraction_method: str | None = None
    acquisition_method: str | None = None
    raw_artifact_ref: str | None = None
    content_sha256: str | None = None
    normalized_sha256: str | None = None
    quality: float | None = None
    provenance: dict[str, Any] = field(default_factory=dict)
    policy_state: str | None = None
    extractor_version: str | None = None

    def __init__(
        self,
        observation_id: str,
        *args,
        source_id: str | None = None,
        source_url: str | None = None,
        content: str | None = None,
        observed_at: datetime | None = None,
        source_family_id: str | None = None,
        document_version_id: str | None = None,
        retrieved_at: datetime | None = None,
        published_at: datetime | None = None,
        author: str | None = None,
        language: str | None = None,
        title: str | None = None,
        structured_data: Any = None,
        evidence_spans: tuple[Any, ...] = (),
        extraction_method: str | None = None,
        acquisition_method: str | None = None,
        raw_artifact_ref: str | None = None,
        content_sha256: str | None = None,
        normalized_sha256: str | None = None,
        quality: float | None = None,
        provenance: dict[str, Any] | None = None,
        policy_state: str | None = None,
        extractor_version: str | None = None,
    ):
        if args:
            if any(value is not None for value in (source_id, source_url, content, observed_at)):
                raise TypeError("ambiguous observation arguments")
            if len(args) == 2:
                source_url, content = args
            elif len(args) == 3:
                source_url, content, observed_at = args
            elif len(args) == 4:
                source_id, source_url, content, observed_at = args
            else:
                raise TypeError("Observation expects 3, 4, 5, or 6 total positional arguments")
        if source_url is None or content is None:
            raise TypeError("source_url and content are required")
        object.__setattr__(self, "observation_id", observation_id)
        object.__setattr__(self, "source_url", source_url)
        object.__setattr__(self, "content", content)
        object.__setattr__(self, "observed_at", observed_at or datetime.now(timezone.utc))
        object.__setattr__(self, "source_id", source_id)
        object.__setattr__(self, "source_family_id", source_family_id)
        object.__setattr__(self, "document_version_id", document_version_id)
        object.__setattr__(self, "retrieved_at", retrieved_at)
        object.__setattr__(self, "published_at", published_at)
        object.__setattr__(self, "author", author)
        object.__setattr__(self, "language", language)
        object.__setattr__(self, "title", title)
        object.__setattr__(self, "structured_data", structured_data)
        object.__setattr__(self, "evidence_spans", tuple(evidence_spans))
        object.__setattr__(self, "extraction_method", extraction_method)
        object.__setattr__(self, "acquisition_method", acquisition_method)
        object.__setattr__(self, "raw_artifact_ref", raw_artifact_ref)
        object.__setattr__(self, "content_sha256", content_sha256)
        object.__setattr__(self, "normalized_sha256", normalized_sha256)
        object.__setattr__(self, "quality", quality)
        object.__setattr__(self, "provenance", dict(provenance or {}))
        object.__setattr__(self, "policy_state", policy_state)
        object.__setattr__(self, "extractor_version", extractor_version)
        self.validate()

    @classmethod
    def create(cls, observation_id, *args, **kwargs):
        if args:
            if any(key in kwargs for key in ("source_url", "content", "source_id", "observed_at")):
                raise TypeError("ambiguous observation arguments")
            if len(args) == 2:
                kwargs["source_url"], kwargs["content"] = args
            elif len(args) == 3:
                kwargs["source_id"], kwargs["source_url"], kwargs["content"] = args
            elif len(args) == 4:
                kwargs["source_id"], kwargs["source_url"], kwargs["content"], kwargs["observed_at"] = args
            else:
                raise TypeError("Observation.create expects 3, 4, or 5 positional arguments")
        return cls(observation_id, **kwargs)

    def validate(self) -> None:
        for name, value, limit in (("observation_id", self.observation_id, 128),
                                    ("source_url", self.source_url, 4096),
                                    ("content", self.content, 2_000_000)):
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must not be empty")
            if len(value) > limit:
                raise ValueError(f"{name} exceeds bounded length")
        for name, value in (("source_id", self.source_id), ("source_family_id", self.source_family_id),
                            ("document_version_id", self.document_version_id), ("author", self.author),
                            ("language", self.language), ("title", self.title),
                            ("extraction_method", self.extraction_method), ("acquisition_method", self.acquisition_method),
                            ("raw_artifact_ref", self.raw_artifact_ref), ("content_sha256", self.content_sha256),
                            ("normalized_sha256", self.normalized_sha256), ("policy_state", self.policy_state),
                            ("extractor_version", self.extractor_version)):
            if value is not None and (not isinstance(value, str) or len(value) > 4096):
                raise ValueError(f"{name} exceeds bounded length")
        if self.quality is not None and not (0.0 <= self.quality <= 1.0):
            raise ValueError("quality must be between 0 and 1")
        if self.content_sha256 is not None:
            actual = sha256(self.content.encode("utf-8")).hexdigest()
            if self.content_sha256 != actual:
                raise ValueError("content_sha256 does not match content")
        json.dumps(self.structured_data, sort_keys=True, default=str)
        json.dumps(self.provenance, sort_keys=True, default=str)

    def fingerprint(self) -> str:
        self.validate()
        payload = {
            "observation_id": self.observation_id,
            "source_url": self.source_url,
            "content_sha256": self.content_sha256 or sha256(self.content.encode("utf-8")).hexdigest(),
            "observed_at": self.observed_at.isoformat(),
            "source_id": self.source_id,
            "source_family_id": self.source_family_id,
            "document_version_id": self.document_version_id,
            "retrieved_at": self.retrieved_at.isoformat() if self.retrieved_at else None,
            "published_at": self.published_at.isoformat() if self.published_at else None,
            "author": self.author,
            "language": self.language,
            "title": self.title,
            "extraction_method": self.extraction_method,
            "acquisition_method": self.acquisition_method,
            "raw_artifact_ref": self.raw_artifact_ref,
            "normalized_sha256": self.normalized_sha256,
            "quality": self.quality,
            "provenance": self.provenance,
            "policy_state": self.policy_state,
            "extractor_version": self.extractor_version,
        }
        encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
        return sha256(encoded).hexdigest()


@dataclass(frozen=True)
class EvidenceSpan:
    observation_id: str
    start: int
    end: int

    def validate(self, observation: Observation):
        if self.observation_id != observation.observation_id:
            raise ValueError("observation ID mismatch")
        if self.start < 0 or self.end < self.start:
            raise ValueError("invalid evidence span")
        if self.end > len(observation.content):
            raise ValueError("evidence span exceeds observation")

    def text_from(self, observation: Observation) -> str:
        self.validate(observation)
        return observation.content[self.start:self.end]
