"""Public Worker chat/service-binding boundary.

Owns private service-binding request construction and chat/dashboard proxy helpers.
HTTP route dispatch remains in worker.py.
"""
from __future__ import annotations

import json

from workers import Response

from backend.worker_auth import bearer_token


class _TestServiceRequest:
    """Minimal request shape used only when the Cloudflare JS runtime is unavailable."""

    def __init__(self, url, *, method, headers, body=None):
        self.url = url
        self.method = method
        self.headers = headers
        self.body = body


def _service_request(url, *, method="GET", headers=None, body=None):
    """Construct the JavaScript Fetch Request object required by an HTTP service binding."""
    request_headers = headers or {}
    try:
        from js import Object, Request as JSRequest
        from pyodide.ffi import to_js

        init = {"method": method, "headers": request_headers}
        if body is not None:
            init["body"] = body
        return JSRequest.new(
            url,
            to_js(init, dict_converter=Object.fromEntries),
        )
    except ImportError:
        return _TestServiceRequest(url, method=method, headers=request_headers, body=body)

def _chat_headers(request):
    headers = {"Content-Type": "application/json"}
    token = _bearer_token(request)
    if token:
        headers["Authorization"] = f"Bearer {token}"
    idempotency_key = request.headers.get("Idempotency-Key")
    if idempotency_key:
        headers["Idempotency-Key"] = idempotency_key
    return headers



async def _public_admit(env, route, subject_fingerprint, event_id):
    db = getattr(env, "DB", None)
    environment = str(getattr(env, "ENVIRONMENT", "production") or "production").casefold()
    local_bypass = str(getattr(env, "LOCAL_DEVELOPMENT_AUTH_BYPASS", "") or "").casefold() == "true"
    if db is None:
        if environment == "development" and local_bypass:
            return AdmissionDecision(
                AdmissionOutcome.ACCEPTED,
                route,
                True,
                "explicit local development admission bypass",
            ), None
        return AdmissionDecision(
            AdmissionOutcome.AUTHORITY_UNAVAILABLE,
            route,
            False,
            "admission authority is unavailable for a protected resource-consuming route",
            AdmissionPolicy().retry_after_seconds,
        ), None
    store = D1AdmissionStore(db)
    return await store.acquire(
        subject_fingerprint=subject_fingerprint,
        route=route,
        policy=AdmissionPolicy(),
        event_id=event_id,
    )


def _admission_response(decision):
    if decision.allowed:
        return None
    status = (
        429
        if decision.outcome in {
            AdmissionOutcome.RATE_LIMITED,
            AdmissionOutcome.CONCURRENCY_LIMITED,
            AdmissionOutcome.DUPLICATE,
        }
        else 503
    )
    response = _authenticated_json(
        {
            "ok": False,
            "error": decision.reason,
            "admission": decision.outcome.value,
            "contract_version": decision.contract_version,
        },
        status=status,
    )
    if decision.retry_after_header:
        response.headers["Retry-After"] = decision.retry_after_header
    return response


async def _operations_chat(env, payload, request):
    """Proxy synchronous Heroic AI chat only through the configured private service binding."""
    operations = getattr(env, "OPERATIONS", None)
    if operations is None:
        return {"ok": False, "error": "chat_backend_unavailable", "status": "unavailable"}, 503
    headers = _chat_headers(request)
    try:
        upstream = await operations.fetch(
            _service_request("https://chat/v1/chat", method="POST", headers=headers, body=json.dumps(payload))
        )
        body = await upstream.json()
        if not isinstance(body, dict):
            return {"ok": False, "error": "invalid_private_chat_response"}, 503
        return body, upstream.status
    except Exception:
        return {"ok": False, "error": "chat_backend_unavailable"}, 503


def _public_sse_response(upstream):
    """Expose only the public SSE headers while preserving the upstream body stream."""
    return Response(
        upstream.body,
        status=int(upstream.status),
        headers={
            "Content-Type": "text/event-stream; charset=utf-8",
            "Cache-Control": "no-store, no-cache, max-age=0, must-revalidate",
            "X-Content-Type-Options": "nosniff",
        },
    )


async def _operations_chat_stream(env, payload, request):
    """Proxy the private chatbot's SSE stream without exposing its topology."""
    operations = getattr(env, "OPERATIONS", None)
    if operations is None:
        return None, {"ok": False, "error": "chat_backend_unavailable", "status": "unavailable"}, 503
    headers = _chat_headers(request)
    try:
        upstream = await operations.fetch(
            _service_request("https://chat/v1/chat/stream", method="POST", headers=headers, body=json.dumps(payload))
        )
        return upstream, None, upstream.status
    except Exception:
        return None, {"ok": False, "error": "chat_backend_unavailable"}, 503


async def _operations_chatbot_diagnostic(env, request=None):
    """Exercise the private chatbot routing/diagnostic boundary without provider execution."""
    operations = getattr(env, "OPERATIONS", None)
    if operations is None:
        return {"ok": False, "error": "chat_backend_unavailable", "status": "unavailable"}, 503
    try:
        headers = {"Content-Type": "application/json"}
        token = _bearer_token(request) if request is not None else None
        if token:
            headers["Authorization"] = f"Bearer {token}"
        upstream = await operations.fetch(
            _service_request(
                "https://private/v1/diagnostics/chatbot",
                method="POST",
                headers=headers,
                body=json.dumps({"operation": "infrastructure_verify", "question": "Infrastructure diagnostic only; do not execute a model provider."}),
            )
        )
        body = await upstream.json()
        healthy = upstream.status == 200 and isinstance(body, dict) and bool(body.get("ok")) and bool(body.get("chatbot", {}).get("allowed"))
        return {
            "ok": healthy,
            "status": "ok" if healthy else "degraded",
            "response_status": upstream.status,
            "chatbot": body.get("chatbot") if isinstance(body, dict) else None,
            "provider_policy": body.get("provider_policy") if isinstance(body, dict) else None,
            "error": None if healthy else (body.get("error") if isinstance(body, dict) else "invalid_private_chatbot_diagnostic"),
        }, 200 if healthy else 503
    except Exception:
        return {"ok": False, "status": "degraded", "error": "chatbot_diagnostic_binding_failure"}, 503


async def _operations_dashboard(env, request):
    """Read-only telemetry proxy for the Heroic AI system dashboard."""
    operations = getattr(env, "OPERATIONS", None)
    if operations is None:
        return {"ok": False, "error": "dashboard_backend_unavailable", "status": "unavailable"}, 503
    headers = {"Content-Type": "application/json"}
    token = _bearer_token(request)
    if token:
        headers["Authorization"] = f"Bearer {token}"
    try:
        upstream = await operations.fetch(_service_request("https://private/v1/dashboard", method="GET", headers=headers))
        body = await upstream.json()
        if not isinstance(body, dict):
            return {"ok": False, "error": "invalid_private_dashboard_response"}, 503
        return body, upstream.status
    except Exception:
        return {"ok": False, "error": "dashboard_backend_unavailable"}, 503

