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
