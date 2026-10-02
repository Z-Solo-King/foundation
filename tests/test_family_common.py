from __future__ import annotations

from pathlib import Path

import pytest

from foundation_core.family_common import (
    Sha256Accumulator,
    canonical_json_bytes,
    dedupe_exact_preserve_order,
    dedupe_preserve_order,
    is_sha256,
    is_sha256_lowercase,
    normalize_casefold_text,
    normalize_unicode_casefold_text,
    require_sha256,
    require_sha256_lowercase,
    sha256_bytes,
    sha256_content,
    sha256_file,
    sha256_json,
    sha256_text,
)


def test_hashing_and_canonical_json_are_deterministic(tmp_path: Path):
    assert canonical_json_bytes({"b": 2, "a": 1}) == b'{"a":1,"b":2}'
    assert sha256_json({"b": 2, "a": 1}) == sha256_json({"a": 1, "b": 2})
    assert sha256_text("hello") == sha256_bytes(b"hello")
    assert sha256_content("hello") == sha256_content(b"hello")


def test_file_and_streaming_hashes_match(tmp_path: Path):
    path = tmp_path / "sample.bin"
    path.write_bytes(b"family-common")
    assert sha256_file(path) == sha256_bytes(b"family-common")

    digest = Sha256Accumulator()
    digest.update(b"family-")
    digest.update(b"common")
    assert digest.hexdigest() == sha256_bytes(b"family-common")


def test_sha_validation_preserves_strictness():
    value = "a" * 64
    assert is_sha256(value)
    assert is_sha256_lowercase(value)
    require_sha256(value, "digest")
    require_sha256_lowercase(value, "digest")

    with pytest.raises(ValueError):
        require_sha256("bad", "digest")
    with pytest.raises(ValueError):
        require_sha256_lowercase("A" * 64, "digest")


def test_generic_dedupe_and_text_normalization_are_stable():
    assert dedupe_exact_preserve_order([" b ", "a", " b ", "a"]) == (" b ", "a")
    assert dedupe_preserve_order([" a ", "b", "a", "", "b"]) == ("a", "b")
    assert normalize_casefold_text("  HELLO   World  ") == "hello world"
    assert normalize_unicode_casefold_text("  KÉ  ") == "ké"
