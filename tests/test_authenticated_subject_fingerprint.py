import hashlib
from types import SimpleNamespace

from backend.worker_auth import authenticated_subject_fingerprint


def test_authenticated_subject_fingerprint_hashes_bearer_token_without_exposing_it():
    request = SimpleNamespace(headers={"Authorization": "Bearer token-a"})
    assert authenticated_subject_fingerprint(request) == hashlib.sha256(b"token-a").hexdigest()
    assert "token-a" not in authenticated_subject_fingerprint(request)


def test_authenticated_subject_fingerprint_returns_none_without_bearer_token():
    assert authenticated_subject_fingerprint(SimpleNamespace(headers={})) is None
    assert authenticated_subject_fingerprint(SimpleNamespace(headers={"Authorization": "Basic token-a"})) is None
