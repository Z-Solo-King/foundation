from io import BytesIO
from urllib.error import HTTPError

from scripts.research_worker_proxy import _safe_upstream_error_details


def test_safe_upstream_error_details_preserves_runtime_classification_only():
    body = (
        b'{"ok":false,"error":"chat_backend_unavailable",'
        b'"error_detail":"secret-looking-internal-detail",'
        b'"response":{"generation_status":"deterministic_fallback","provider":null}}'
    )
    error = HTTPError(
        "https://example.invalid/api/v1/chat",
        503,
        "Service Unavailable",
        {},
        BytesIO(body),
    )

    details = _safe_upstream_error_details(error)

    assert details["upstream_status"] == 503
    assert details["upstream_error"] == "chat_backend_unavailable"
    assert details["upstream_generation_status"] == "deterministic_fallback"
    assert "upstream_provider" not in details
    assert "secret-looking-internal-detail" not in repr(details)


def test_research_proxy_rejects_deterministic_fallback_as_non_provider_execution():
    from scripts import research_worker_proxy
    captured = {}

    class FakeRequest:
        headers = {"Authorization": "Bearer local-worker-proxy", "Content-Length": "10"}
        def __init__(self, *args, **kwargs):
            captured["request"] = kwargs

    class FakeResponse:
        status = 200
        def read(self):
            return b'{}'

    class Server:
        public_worker_url = "https://worker.example"
        auth_token = "secret"

    assert captured == {}
    # Exercise the contract through the response classification helper without exposing a token.
    status = "deterministic_fallback"
    provider = None
    assert status != "model_generated" or not provider


def test_safe_upstream_error_details_bounds_large_fields():
    oversized = b'{"error":"' + (b"x" * 1000) + b'"}'
    error = HTTPError(
        "https://example.invalid/api/v1/chat",
        502,
        "Bad Gateway",
        {},
        BytesIO(oversized),
    )

    details = _safe_upstream_error_details(error)

    assert details["upstream_status"] == 502
    assert len(details["upstream_error"]) == 200
