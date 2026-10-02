"""Public deterministic family primitives shared by Foundation and private Operations.
No network, provider, policy, credential, or execution-authority behavior belongs here.
"""
from __future__ import annotations

from collections.abc import Iterable
from hashlib import sha256
import json
from pathlib import Path
from typing import Any, TypeVar

T = TypeVar("T")


def canonical_json_bytes(value: Any, *, ensure_ascii: bool = False) -> bytes:
    """Encode JSON-compatible data deterministically for fingerprints."""
    return json.dumps(
        value,
        ensure_ascii=ensure_ascii,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    """Return the hexadecimal SHA-256 digest for bytes."""
    return sha256(value).hexdigest()


def sha256_text(value: str) -> str:
    """Return the hexadecimal SHA-256 digest for UTF-8 text."""
    if not isinstance(value, str):
        raise TypeError("hash text must be a string")
    return sha256_bytes(value.encode("utf-8"))


def sha256_content(value: bytes | bytearray | memoryview | str) -> str:
    """Hash textual or byte content using one canonical definition."""
    payload = value.encode("utf-8") if isinstance(value, str) else bytes(value)
    return sha256_bytes(payload)


def sha256_json(value: Any, *, ensure_ascii: bool = False) -> str:
    """Return the hexadecimal SHA-256 digest of canonical JSON."""
    return sha256_bytes(canonical_json_bytes(value, ensure_ascii=ensure_ascii))


def sha256_file(path: Path) -> str:
    """Hash a file incrementally without loading the whole file into memory."""
    digest = sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def is_sha256(value: str | None) -> bool:
    """Return whether a value is exactly a hexadecimal SHA-256 digest."""
    if not isinstance(value, str) or len(value) != 64:
        return False
    return all(char in "0123456789abcdefABCDEF" for char in value)


def is_sha256_lowercase(value: str | None) -> bool:
    """Return whether a value is exactly a lowercase SHA-256 digest."""
    if not isinstance(value, str) or len(value) != 64:
        return False
    return all(char in "0123456789abcdef" for char in value)


def require_sha256(value: str | None, field_name: str) -> None:
    """Raise a bounded validation error when a digest is malformed."""
    if not is_sha256(value):
        raise ValueError(f"{field_name} must be a SHA-256 hex digest")


def require_sha256_lowercase(value: str | None, field_name: str) -> None:
    """Raise a bounded validation error when a lowercase digest is malformed."""
    if not is_sha256_lowercase(value):
        raise ValueError(f"{field_name} must be a lowercase SHA-256 hex digest")


class Sha256Accumulator:
    """Small streaming SHA-256 adapter for bounded consumers."""

    def __init__(self) -> None:
        self._digest = sha256()

    def update(self, chunk: bytes) -> None:
        if not isinstance(chunk, bytes):
            raise TypeError("digest chunks must be bytes")
        self._digest.update(chunk)

    def hexdigest(self) -> str:
        return self._digest.hexdigest()


def dedupe_exact_preserve_order(values: Iterable[T]) -> tuple[T, ...]:
    """Remove exact repeated hashable values while preserving first-seen order."""
    return tuple(dict.fromkeys(values))


def dedupe_preserve_order(values: Iterable[str]) -> tuple[str, ...]:
    """Remove repeated non-empty strings without changing first-seen order."""
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        normalized = str(value).strip()
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        result.append(normalized)
    return tuple(result)


def normalize_casefold_text(value: str) -> str:
    """Normalize ordinary text by trimming, collapsing whitespace, and case-folding."""
    if not isinstance(value, str):
        raise TypeError("text must be a string")
    return " ".join(value.casefold().split())


def normalize_unicode_casefold_text(value: str) -> str:
    """Normalize text with NFKC, whitespace collapsing, and case-folding."""
    if not isinstance(value, str):
        raise TypeError("text must be a string")
    import unicodedata

    return " ".join(unicodedata.normalize("NFKC", value).split()).casefold()


__all__ = [
    "Sha256Accumulator",
    "canonical_json_bytes",
    "dedupe_exact_preserve_order",
    "dedupe_preserve_order",
    "is_sha256",
    "is_sha256_lowercase",
    "normalize_casefold_text",
    "normalize_unicode_casefold_text",
    "require_sha256",
    "require_sha256_lowercase",
    "sha256_bytes",
    "sha256_content",
    "sha256_file",
    "sha256_json",
    "sha256_text",
]
