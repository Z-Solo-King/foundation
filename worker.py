"""Cloudflare Python Worker entrypoint for the standalone public-safe runtime."""
from __future__ import annotations

import hashlib
import hmac
import json
import logging
import os
import uuid
from datetime import datetime, timezone
from urllib.parse import parse_qs, urlparse

from workers import Response, WorkerEntrypoint

_LOGGER = logging.getLogger("foundation.worker")

from backend.api.main import submit_research
from backend.api.models import ChatRequest, ResearchRequest
from backend.admission import AdmissionDecision, AdmissionOutcome, AdmissionPolicy, AdmissionRoute
from backend.admission_store import D1AdmissionStore
from backend.evidence_publication import package_digest, verify_package
from backend.persistence.cloudflare import CloudflarePersistence
from backend.public_read_cursor import PublicReadCursorError
from backend.sources.http import fetch_public_url
from backend.worker_auth import MAX_PUBLIC_JSON_BODY_BYTES, authenticated_subject_fingerprint, authorized, bearer_token, extract_source_urls, json_object
from backend.worker_diagnostics import health_payload, public_infrastructure_verify, readiness_payload, storage_diagnostic
from backend.worker_research import get_run, ingest_sources



class _TestServiceRequest:
    """Minimal request shape used only when the Cloudflare JS runtime is unavailable."""

    def __init__(self, url, *, method, headers, body=None):
        self.url = url
        self.method = method
        self.headers = headers
        self.body = body


def _service_request(url, *, method="GET", headers=None, body=None, signal=None):
    """Construct the JavaScript Fetch Request object required by an HTTP service binding."""
    request_headers = headers or {}
    try:
        from js import Object, Request as JSRequest
        from pyodide.ffi import to_js

        init = {"method": method, "headers": request_headers}
        if body is not None:
            init["body"] = body
        if signal is not None:
            init["signal"] = signal
        return JSRequest.new(
            url,
            to_js(init, dict_converter=Object.fromEntries),
        )
    except ImportError:
        return _TestServiceRequest(url, method=method, headers=request_headers, body=body)
def _extract_source_urls(question, explicit=()):
    return extract_source_urls(question, explicit)


def _bearer_token(request):
    return bearer_token(request)


def _authorized(request, env):
    return authorized(request, env)


async def _json(request):
    return await json_object(request)


async def _health_payload(env=None):
    return health_payload(env)


async def _readiness_payload(env):
    return await readiness_payload(env)


async def _storage_diagnostic(env, run_id):
    return await storage_diagnostic(env, run_id, persistence_cls=CloudflarePersistence)


async def _public_infrastructure_verify(env):
    return await public_infrastructure_verify(env, persistence_cls=CloudflarePersistence)


async def _ingest_sources(env, run_id, req):
    return await ingest_sources(env, run_id, req, fetcher=fetch_public_url, persistence_cls=CloudflarePersistence)


async def _get_run(
    env,
    run_id,
    *,
    subject_fingerprint="development-local",
    cursor=None,
    limit=50,
    cursor_secret="development-local",
):
    return await get_run(
        env,
        run_id,
        subject_fingerprint=subject_fingerprint,
        cursor=cursor,
        limit=limit,
        cursor_secret=cursor_secret,
    )


async def _publish_evidence(env, run_id, package):
    """Accept only a signed, digest-verified package whose lineage belongs to run_id."""
    run = await env.DB.prepare("SELECT run_id FROM research_runs WHERE run_id = ?").bind(run_id).first()
    if not run:
        return {"ok": False, "error": "run not found"}, 404
    rows = await env.DB.prepare("SELECT observation_id FROM observations WHERE run_id = ?").bind(run_id).all()
    observed_ids = {str(row["observation_id"] if isinstance(row, dict) else row.observation_id) for row in rows}
    secret = str(getattr(env, "EVIDENCE_PACKAGE_SIGNING_SECRET", "") or os.getenv("EVIDENCE_PACKAGE_SIGNING_SECRET", ""))
    valid, reason = verify_package(package, secret=secret, run_id=run_id, observed_ids=observed_ids)
    if not valid:
        return {"ok": False, "error": reason, "publication_state": "rejected"}, 400
    digest = package_digest(package)
    published_at = datetime.now(timezone.utc).isoformat()
    serialized = json.dumps(package, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    result = await env.DB.prepare(
        "INSERT INTO research_publications (run_id, package_digest, package_json, published_at) VALUES (?, ?, ?, ?)"
    ).bind(run_id, digest, serialized, published_at).run()
    publication_id = None
    if isinstance(result, dict):
        publication_id = result.get("meta", {}).get("last_row_id")
    return {
        "ok": True,
        "run_id": run_id,
        "publication_id": publication_id,
        "publication_state": "published",
        "package_digest": digest,
        "published_at": published_at,
    }, 200


def _authenticated_json(payload, *, status=200):
    """Return a bounded authenticated response that cannot be shared or reused by caches."""
    serialized = json.dumps(payload, ensure_ascii=False)
    if len(serialized.encode("utf-8")) > MAX_PUBLIC_JSON_BODY_BYTES:
        serialized = json.dumps({"ok": False, "error": "response exceeds supported size"}, ensure_ascii=False)
        status = 500
    return Response(
        serialized,
        status=status,
        headers={
            "Content-Type": "application/json",
            "Cache-Control": "private, no-store, max-age=0, must-revalidate",
        },
    )


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
            _service_request(
                "https://chat/v1/chat",
                method="POST",
                headers=headers,
                body=json.dumps(payload),
                signal=getattr(request, "signal", None),
            )
        )
        body = await upstream.json()
        if not isinstance(body, dict):
            return {"ok": False, "error": "invalid_private_chat_response"}, 503
        return body, upstream.status
    except Exception as exc:
        return {
            "ok": False,
            "error": "chat_backend_unavailable",
            "error_class": type(exc).__name__,
            "error_detail": str(exc)[:240],
        }, 503


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


def _chat_sse_body(body):
    """Build bounded SSE frames at the public edge from a completed private JSON response."""
    response = body.get("response") if isinstance(body, dict) else None
    if not isinstance(response, dict):
        raise ValueError("invalid_private_chat_response")
    response_id = str(response.get("response_id", "")).strip()
    if not response_id:
        raise ValueError("stream_execution_identity_missing")
    result_state = str(response.get("result_state", "BLOCKED")).upper()
    if result_state == "BLOCKED":
        raise ValueError("blocked_chat_stream")
    text = str(response.get("text", ""))
    events = [
        f"event: start\ndata: {json.dumps({'response_id': response_id, 'status': 'streaming', 'generation': response.get('generation_status', 'unknown')}, separators=(',', ':'))}\n\n"
    ]
    for offset in range(0, len(text), 256):
        chunk = text[offset:offset + 256]
        events.append(
            f"event: delta\ndata: {json.dumps({'text': chunk}, separators=(',', ':'))}\n\n"
        )
    usage = response.get("usage")
    if isinstance(usage, dict):
        events.append(
            f"event: usage\ndata: {json.dumps({'input_tokens': usage.get('input_tokens'), 'output_tokens': usage.get('output_tokens')}, separators=(',', ':'))}\n\n"
        )
    output_digest = __import__("hashlib").sha256(text.encode("utf-8")).hexdigest()
    status = "completed" if result_state == "COMPLETE" else "partial"
    events.append(
        f"event: done\ndata: {json.dumps({'response_id': response_id, 'status': status, 'result_state': result_state, 'output_digest': output_digest}, separators=(',', ':'))}\n\n"
    )
    payload = "".join(events)
    if len(payload.encode("utf-8")) > MAX_PUBLIC_JSON_BODY_BYTES:
        raise ValueError("stream response exceeds supported size")
    return payload


async def _operations_chat_stream(env, payload, request):
    """Obtain the proven JSON chat result while preserving client cancellation to Operations."""
    body, status = await _operations_chat(env, payload, request)
    return body, status


async def _operations_chatbot_diagnostic(env, request=None, operation="infrastructure_verify", payload=None):
    """Exercise the private chatbot routing/diagnostic boundary without provider execution."""
    operations = getattr(env, "OPERATIONS", None)
    if operations is None:
        return {"ok": False, "error": "chat_backend_unavailable", "status": "unavailable"}, 503
    try:
        headers = {"Content-Type": "application/json"}
        token = _bearer_token(request) if request is not None else None
        if token:
            headers["Authorization"] = f"Bearer {token}"
        diagnostic_payload = {
            "operation": operation,
            "question": "Infrastructure diagnostic only; do not execute a model provider.",
        }
        if operation in {"persistence_seed", "persistence_verify"} and isinstance(payload, dict):
            sentinel_id = str(payload.get("sentinel_id", "")).strip()
            if sentinel_id:
                diagnostic_payload["sentinel_id"] = sentinel_id
        upstream = await operations.fetch(
            _service_request(
                "https://private/v1/diagnostics/chatbot",
                method="POST",
                headers=headers,
                body=json.dumps(diagnostic_payload),
            )
        )
        body = await upstream.json()
        body_dict = body if isinstance(body, dict) else {}
        if operation in {"persistence_seed", "persistence_verify"}:
            return body_dict, upstream.status
        runtime_checks = body_dict.get("runtime_checks") if isinstance(body_dict.get("runtime_checks"), list) else []
        runtime_ok = bool(body_dict.get("runtime_status") == "ok") and bool(runtime_checks) and all(
            isinstance(check, dict) and bool(check.get("ok"))
            for check in runtime_checks
        )
        chatbot = body_dict.get("chatbot")
        chatbot_allowed = isinstance(chatbot, dict) and bool(chatbot.get("allowed"))
        healthy = (
            upstream.status == 200
            and isinstance(body, dict)
            and bool(body_dict.get("ok"))
            and chatbot_allowed
            and runtime_ok
        )
        return {
            "ok": healthy,
            "status": "ok" if healthy else "degraded",
            "response_status": upstream.status,
            "chatbot": body.get("chatbot") if isinstance(body, dict) else None,
            "provider_policy": body.get("provider_policy") if isinstance(body, dict) else None,
            "runtime_status": body.get("runtime_status") if isinstance(body, dict) else None,
            "runtime_checks": runtime_checks,
            "error": None if healthy else (body.get("error") if isinstance(body, dict) else "invalid_private_chatbot_diagnostic"),
        }, 200 if healthy else 503
    except Exception as exc:
        return {"ok": False, "status": "degraded", "error": f"chatbot diagnostic binding failure: {exc}"}, 503


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


class Default(WorkerEntrypoint):
    async def fetch(self, request):
        path = request.url.split("?", 1)[0]

        if request.method == "GET" and path.endswith("/health"):
            return Response.json(await _health_payload(self.env))
        if request.method == "GET" and path.endswith("/readiness"):
            payload, status = await _readiness_payload(self.env)
            return Response.json(payload, status=status)
        if request.method == "GET" and path.endswith("/api/v1/dashboard"):
            if not _authorized(request, self.env):
                return _authenticated_json({"ok": False, "error": "unauthorized"}, status=401)
            body, status = await _operations_dashboard(self.env, request)
            return _authenticated_json(body, status=status)
        if request.method == "POST" and path.endswith("/api/v1/chat/stream"):
            if not _authorized(request, self.env):
                return _authenticated_json({"ok": False, "error": "unauthorized"}, status=401)
            payload = await _json(request)
            if payload is None:
                return _authenticated_json({"ok": False, "error": "invalid JSON object"}, status=400)
            try:
                req = ChatRequest(**payload)
                req.validate()
            except (TypeError, ValueError) as exc:
                return _authenticated_json({"ok": False, "error": str(exc)}, status=400)
            subject = authenticated_subject_fingerprint(request) or "development-local"
            event_id = request.headers.get("Idempotency-Key") or req.request_id or uuid.uuid4().hex
            decision, lease = await _public_admit(self.env, AdmissionRoute.STREAM, subject, event_id)
            denied = _admission_response(decision)
            if denied is not None:
                return denied
            try:
                body, status = await _operations_chat_stream(self.env, payload, request)
                if status != 200:
                    return _authenticated_json(body, status=status)
                try:
                    stream_body = _chat_sse_body(body)
                except ValueError as exc:
                    return _authenticated_json({"ok": False, "error": str(exc)}, status=503)
                return Response(
                    stream_body,
                    status=200,
                    headers={
                        "Content-Type": "text/event-stream; charset=utf-8",
                        "Cache-Control": "no-store, no-cache, max-age=0, must-revalidate",
                        "X-Content-Type-Options": "nosniff",
                    },
                )
            finally:
                if lease is not None:
                    await D1AdmissionStore(self.env.DB).release(lease)
        if request.method == "POST" and path.endswith("/api/v1/chat"):
            if not _authorized(request, self.env):
                return _authenticated_json({"ok": False, "error": "unauthorized"}, status=401)
            payload = await _json(request)
            if payload is None:
                return _authenticated_json({"ok": False, "error": "invalid JSON object"}, status=400)
            try:
                req = ChatRequest(**payload)
                req.validate()
            except (TypeError, ValueError) as exc:
                return _authenticated_json({"ok": False, "error": str(exc)}, status=400)
            subject = authenticated_subject_fingerprint(request) or "development-local"
            event_id = request.headers.get("Idempotency-Key") or req.request_id or uuid.uuid4().hex
            decision, lease = await _public_admit(self.env, AdmissionRoute.CHAT, subject, event_id)
            denied = _admission_response(decision)
            if denied is not None:
                return denied
            try:
                body, status = await _operations_chat(self.env, payload, request)
                return _authenticated_json(body, status=status)
            finally:
                if lease is not None:
                    await D1AdmissionStore(self.env.DB).release(lease)
        if request.method == "POST" and path.endswith("/api/v1/chatbot/diagnostic"):
            if not _authorized(request, self.env):
                return _authenticated_json({"ok": False, "error": "unauthorized"}, status=401)
            payload = await _json(request)
            if payload is None:
                return _authenticated_json({"ok": False, "error": "invalid JSON object"}, status=400)
            operation = payload.get("operation")
            if operation == "infrastructure_verify_public_test":
                body, status = await _public_infrastructure_verify(self.env)
                private_body, private_status = await _operations_chatbot_diagnostic(
                    self.env, request, operation="infrastructure_verify"
                )
                body["checks"].append({
                    "name": "public_chatbot",
                    "ok": private_body.get("ok", False),
                    "status": private_status,
                    "detail": private_body.get("error") or "private chatbot diagnostic completed",
                    "runtime_status": private_body.get("runtime_status"),
                    "runtime_checks": private_body.get("runtime_checks", []),
                })
                body["ok"] = all(bool(check.get("ok")) for check in body["checks"])
                body["status"] = "ok" if body["ok"] else "degraded"
                return _authenticated_json(body, status=200 if body["ok"] else 503)
            if operation in {"persistence_seed", "persistence_verify"}:
                private_body, private_status = await _operations_chatbot_diagnostic(
                    self.env, request, operation=operation, payload=payload
                )
                return _authenticated_json(private_body, status=private_status)
            return _authenticated_json({"ok": False, "error": "unsupported public diagnostic operation"}, status=400)
        if request.method == "POST" and path.endswith("/api/v1/storage/diagnostic"):
            if not _authorized(request, self.env):
                return _authenticated_json({"ok": False, "error": "unauthorized"}, status=401)
            payload = await _json(request)
            if payload is None or not payload.get("run_id"):
                return _authenticated_json({"ok": False, "error": "run_id is required"}, status=400)
            try:
                body, status = await _storage_diagnostic(self.env, str(payload["run_id"]))
                return _authenticated_json(body, status=status)
            except Exception as exc:
                return _authenticated_json({"ok": False, "error": f"storage diagnostic failure: {exc}"}, status=503)
        if request.method == "POST" and path.endswith("/api/v1/research/publish"):
            if not _authorized(request, self.env):
                return _authenticated_json({"ok": False, "error": "unauthorized"}, status=401)
            payload = await _json(request)
            if payload is None or not payload.get("run_id"):
                return _authenticated_json({"ok": False, "error": "run_id is required"}, status=400)
            package = payload.get("package")
            body, status = await _publish_evidence(self.env, str(payload["run_id"]), package)
            return _authenticated_json(body, status=status)
        if request.method == "GET" and "/api/v1/research/" in path:
            if not _authorized(request, self.env):
                return _authenticated_json({"ok": False, "error": "unauthorized"}, status=401)
            run_id = path.rsplit("/", 1)[-1]
            query = parse_qs(urlparse(request.url).query)
            cursor = query.get("cursor", [None])[0]
            limit_raw = query.get("limit", ["50"])[0]
            try:
                limit = int(limit_raw)
            except (TypeError, ValueError):
                return _authenticated_json({"ok": False, "error": "limit must be an integer"}, status=400)
            if limit < 1 or limit > 50:
                return _authenticated_json({"ok": False, "error": "limit must be between 1 and 50"}, status=400)
            subject_fingerprint = authenticated_subject_fingerprint(request) or "development-local"
            try:
                payload = await _get_run(
                    self.env,
                    run_id,
                    subject_fingerprint=subject_fingerprint,
                    cursor=cursor,
                    limit=limit,
                    cursor_secret=(
                        hmac.new(
                            (bearer_token(request) or "development-local").encode("utf-8"),
                            b"foundation-public-read-cursor:v1",
                            hashlib.sha256,
                        ).hexdigest()
                    ),
                )
            except PublicReadCursorError as exc:
                return _authenticated_json({"ok": False, "error": str(exc)}, status=400)
            except Exception as exc:
                return _authenticated_json({"ok": False, "error": f"persistence failure: {exc}"}, status=503)
            if payload is None:
                return _authenticated_json({"ok": False, "error": "run not found"}, status=404)
            return _authenticated_json({"ok": True, **payload})
        if request.method == "POST" and path.endswith("/api/v1/research"):
            if not _authorized(request, self.env):
                return _authenticated_json({"ok": False, "error": "unauthorized"}, status=401)
            payload = await _json(request)
            if payload is None:
                return _authenticated_json({"ok": False, "error": "invalid JSON object"}, status=400)
            payload = dict(payload)
            question = str(payload.get("question") or "")
            payload["source_urls"] = list(_extract_source_urls(question, payload.get("source_urls") or ()))
            try:
                req = ResearchRequest(**payload)
            except TypeError as exc:
                return _authenticated_json({"ok": False, "error": str(exc)}, status=400)
            subject_fingerprint = authenticated_subject_fingerprint(request) or "development-local"
            event_id = request.headers.get("Idempotency-Key") or f"research:{uuid.uuid4().hex}"
            decision, lease = await _public_admit(self.env, AdmissionRoute.RESEARCH, subject_fingerprint, event_id)
            denied = _admission_response(decision)
            if denied is not None:
                return denied
            result = submit_research(req)
            if not result.ok:
                if lease is not None:
                    await D1AdmissionStore(self.env.DB).release(lease)
                return _authenticated_json({"ok": False, "error": result.error}, status=400)
            persistence = CloudflarePersistence(self.env)
            subject_fingerprint = authenticated_subject_fingerprint(request) or "development-local"
            idempotency_key = request.headers.get("Idempotency-Key")
            run_id = None
            phase = "create_run"
            try:
                if idempotency_key:
                    run_id = await persistence.create_run_idempotent(req, idempotency_key, subject_fingerprint=subject_fingerprint)
                else:
                    run_id = result.run_id
                    create_scoped = getattr(persistence, "create_run_scoped", None)
                    if callable(create_scoped):
                        await create_scoped(run_id, req, subject_fingerprint)
                    else:
                        await persistence.create_run(run_id, req)
                if not req.source_urls:
                    return _authenticated_json({"ok": True, "run_id": run_id, "metadata": {**result.metadata, "execution_mode": "awaiting_source_urls", "source_url_ingestion": True, "general_web_discovery": False, "evidence_synthesis": False, "next_action": "provide one or more permitted public HTTP(S) source URLs"}, "sources": []})
                phase = "set_running"
                await persistence.set_run_status(run_id, "running")
                phase = "ingest"
                sources = await _ingest_sources(self.env, run_id, req)
                phase = "set_completed"
                await persistence.set_run_status(run_id, "completed")
            except Exception as exc:
                if run_id is not None:
                    try:
                        await persistence.set_run_status(run_id, "failed")
                    except Exception:
                        _LOGGER.exception("failed to record terminal failed status for run_id=%s", run_id)
                return _authenticated_json({
                    "ok": False,
                    "error": "execution/persistence failure",
                    "phase": phase,
                    "error_class": type(exc).__name__,
                }, status=503)
            finally:
                if lease is not None:
                    await D1AdmissionStore(self.env.DB).release(lease)
            return _authenticated_json({"ok": True, "run_id": run_id, "metadata": {**result.metadata, "execution_mode": "source_url_ingestion"}, "sources": sources})
        assets = getattr(self.env, "ASSETS", None)
        if assets is not None:
            response = await assets.fetch(request)
            headers = dict(response.headers)
            headers["Content-Security-Policy"] = (
                "default-src 'self'; script-src 'self'; style-src 'self'; "
                "img-src 'self' data: blob:; connect-src 'self'; object-src 'none'; "
                "base-uri 'self'; frame-ancestors 'none'; form-action 'self'"
            )
            headers["X-Frame-Options"] = "DENY"
            headers["Referrer-Policy"] = "no-referrer"
            headers["X-Content-Type-Options"] = "nosniff"
            return Response(response.body, status=response.status, headers=headers)
        return _authenticated_json({"ok": False, "error": "not found"}, status=404)
