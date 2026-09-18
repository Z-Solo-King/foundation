import pytest

from backend.intelligence.source_integrity import (
    IntegrityState,
    SourceIdentity,
    classify_source_integrity,
)


def identity(url="https://example.com/page", body=b"hello", family="example.com"):
    return SourceIdentity.from_content(url, body, family_key=family)


def test_first_trusted_source_is_eligible():
    candidate = identity()
    assert classify_source_integrity(
        candidate,
        observed_family_hashes={},
        trusted_family_keys={"example.com"},
    ) is IntegrityState.ELIGIBLE


def test_same_family_and_content_is_not_independent_corroboration():
    candidate = identity(url="https://mirror.example/page")
    assert classify_source_integrity(
        candidate,
        observed_family_hashes={"example.com": candidate.content_hash},
        trusted_family_keys={"example.com"},
    ) is IntegrityState.DUPLICATE_FAMILY


def test_modified_family_content_is_explicit():
    candidate = identity(body=b"changed")
    assert classify_source_integrity(
        candidate,
        observed_family_hashes={"example.com": "old"},
        trusted_family_keys={"example.com"},
    ) is IntegrityState.MODIFIED


def test_untrusted_family_fails_closed():
    candidate = identity(family="unknown.example")
    assert classify_source_integrity(
        candidate,
        observed_family_hashes={},
        trusted_family_keys={"example.com"},
    ) is IntegrityState.UNTRUSTED


def test_invalid_url_is_rejected():
    with pytest.raises(ValueError):
        identity(url="not-a-url")


def test_blank_family_key_is_rejected():
    with pytest.raises(ValueError, match="family_key"):
        identity(family=" ")



def test_empty_source_url_is_rejected():
    with pytest.raises(ValueError, match="source URL"):
        identity(url="   ")


def test_same_content_different_family_is_not_independent():
    candidate = identity(url="https://mirror.example/page", body=b"hello", family="mirror.example")
    assert classify_source_integrity(
        candidate,
        observed_family_hashes={},
        observed_content_hashes={candidate.content_hash},
        trusted_family_keys={"mirror.example"},
    ) is IntegrityState.DUPLICATE_CONTENT


def test_new_family_without_content_history_remains_eligible():
    candidate = identity(url="https://mirror.example/page", body=b"hello", family="mirror.example")
    assert classify_source_integrity(
        candidate,
        observed_family_hashes={},
        trusted_family_keys={"mirror.example"},
    ) is IntegrityState.ELIGIBLE
