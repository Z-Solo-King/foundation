"""Canonical content-hash helper used by evidence verification."""

import hashlib


def sha256_text(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


__all__ = ["sha256_text"]
