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

def test_authenticated_subject_fingerprint_uses_signed_release_scope_without_exposing_secret():
    import hmac
    request = SimpleNamespace(headers={
        "Authorization": "Bearer token-a",
        "X-Heroic-Release-ID": "run-123",
        "X-Heroic-Release-Signature": hmac.new(
            b"token-a",
            b"heroic-release-v1:run-123",
            "sha256",
        ).hexdigest(),
    })
    runtime = SimpleNamespace(ENVIRONMENT="production", AUTH_TOKEN="token-a")
    first = authenticated_subject_fingerprint(request, runtime)
    assert first != hashlib.sha256(b"token-a").hexdigest()
    assert "token-a" not in first


def test_invalid_release_signature_falls_back_to_operator_subject():
    request = SimpleNamespace(headers={
        "Authorization": "Bearer token-a",
        "X-Heroic-Release-ID": "run-123",
        "X-Heroic-Release-Signature": "0" * 64,
    })
    runtime = SimpleNamespace(ENVIRONMENT="production", AUTH_TOKEN="token-a")
    assert authenticated_subject_fingerprint(request, runtime) == hashlib.sha256(b"token-a").hexdigest()
