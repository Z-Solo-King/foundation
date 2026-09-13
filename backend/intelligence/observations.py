from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from hashlib import sha256
import json
from typing import Any


@dataclass(frozen=True, init=False)
class Observation:
    """Canonical provenance-preserving observation record."""

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

    def __init__(self, observation_id: str, *args, **kwargs):
        source_id = source_url = content = observed_at = None
        positional = tuple(args)
        if positional:
            if any(key in kwargs for key in ("source_url", "content", "source_id", "observed_at")):
                raise TypeError("ambiguous observation arguments")
            if len(positional) == 4:
                source_id, source_url, content, observed_at = positional
            elif len(positional) == 3:
                source_url, content, observed_at = positional
            elif len(positional) == 2 and kwargs:
                source_url, content = positional
            else:
                raise TypeError("Observation expects 4 or 5 total positional arguments")
        else:
            source_id = kwargs.pop("source_id", None)
            source_url = kwargs.pop("source_url", None)
            content = kwargs.pop("content", None)
            observed_at = kwargs.pop("observed_at", None)
        if positional and len(positional) == 3:
            source_id = None
        observed_at = observed_at or datetime.now(timezone.utc)
        if source_url is None or content is None:
            raise TypeError("source_url and content are required")
        object.__setattr__(self, "observation_id", observation_id)
        object.__setattr__(self, "source_url", source_url)
        object.__setattr__(self, "content", content)
        object.__setattr__(self, "observed_at", observed_at)
        defaults = {
            "source_id": source_id, "source_family_id": None, "document_version_id": None,
            "retrieved_at": None, "published_at": None, "author": None, "language": None,
            "title": None, "structured_data": None, "evidence_spans": (), "extraction_method": None,
            "acquisition_method": None, "raw_artifact_ref": None, "content_sha256": None,
            "normalized_sha256": None, "quality": None, "provenance": {}, "policy_state": None,
            "extractor_version": None,
        }
        for name, default in defaults.items():
            value = kwargs.pop(name, default)
            if name == "evidence_spans":
                value = tuple(value or ())
            if name == "provenance":
                value = dict(value or {})
            object.__setattr__(self, name, value)
        if kwargs:
            raise TypeError(f"unexpected observation fields: {', '.join(sorted(kwargs))}")
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
        for name in ("source_id", "source_family_id", "document_version_id", "author", "language", "title",
                     "extraction_method", "acquisition_method", "raw_artifact_ref", "content_sha256",
                     "normalized_sha256", "policy_state", "extractor_version"):
            value = getattr(self, name)
            if value is not None and (not isinstance(value, str) or len(value) > 4096):
                raise ValueError(f"{name} exceeds bounded length")
        if self.quality is not None and not (0.0 <= self.quality <= 1.0):
            raise ValueError("quality must be between 0 and 1")
        if self.content_sha256 is not None and self.content_sha256 != sha256(self.content.encode("utf-8")).hexdigest():
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
        return sha256(json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")).hexdigest()


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
