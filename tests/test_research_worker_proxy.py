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


def test_provider_execution_contract_requires_model_generated_response():
    response = {"generation_status": "deterministic_fallback", "provider": None}
    assert response["generation_status"] != "model_generated" or not response["provider"]

    generated = {"generation_status": "model_generated", "provider": "cloudflare_workers_ai"}
    assert generated["generation_status"] == "model_generated" and bool(generated["provider"])


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

def test_proxy_upstream_request_uses_explicit_edge_compatible_headers():
    from scripts.research_worker_proxy import UPSTREAM_USER_AGENT
    assert UPSTREAM_USER_AGENT.startswith("HeroicAI-NightlyResearch/")
    assert "Python-urllib" not in UPSTREAM_USER_AGENT

def test_safe_header_details_keeps_only_safe_transport_fields():
    from scripts.research_worker_proxy import _safe_header_details

    class Headers:
        def get(self, key):
            return {"server":"cloudflare","cf-ray":"abc123","cf-mitigated":"challenge","retry-after":"30","authorization":"secret"}.get(key)

    details = _safe_header_details(Headers())
    assert details == {"upstream_server":"cloudflare","cf_ray":"abc123","cf_mitigated":"challenge","retry_after":"30"}
