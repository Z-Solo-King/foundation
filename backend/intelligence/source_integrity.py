"""Deterministic content-integrity and source-family classification."""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from enum import StrEnum
from urllib.parse import urlsplit


class IntegrityState(StrEnum):
    ELIGIBLE = "eligible"
    DUPLICATE_FAMILY = "duplicate_family"
    MODIFIED = "modified"
    UNTRUSTED = "untrusted"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class SourceIdentity:
    url: str
    family_key: str
    content_hash: str

    @classmethod
    def from_content(cls, url: str, content: bytes, *, family_key: str | None = None) -> "SourceIdentity":
        normalized = url.strip()
        if not normalized:
            raise ValueError("source URL must not be empty")
        parts = urlsplit(normalized)
        host = (parts.hostname or "").casefold()
        if not host:
            raise ValueError("source URL must contain a hostname")
        family = family_key.strip() if family_key else host
        if not family:
            raise ValueError("family_key must not be empty")
        return cls(normalized, family, hashlib.sha256(content).hexdigest())


def classify_source_integrity(
    candidate: SourceIdentity,
    *,
    observed_family_hashes: dict[str, str],
    trusted_family_keys: set[str],
) -> IntegrityState:
    if candidate.family_key not in trusted_family_keys:
        return IntegrityState.UNTRUSTED
    previous = observed_family_hashes.get(candidate.family_key)
    if previous is None:
        return IntegrityState.ELIGIBLE
    if previous == candidate.content_hash:
        return IntegrityState.DUPLICATE_FAMILY
    return IntegrityState.MODIFIED
