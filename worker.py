"""Cloudflare Python Worker entrypoint for the standalone public-safe runtime."""
from __future__ import annotations

import hashlib  # Compatibility export used by legacy worker diagnostics tests.
import json

from workers import Response, WorkerEntrypoint

from backend.api.main import submit_research
from backend.api.models import ChatRequest, ResearchRequest
from backend.persistence.cloudflare import CloudflarePersistence
from backend.sources.http import fetch_public_url
from backend.worker_auth import authorized, bearer_token, extract_source_urls, json_object
from backend.worker_diagnostics import health_payload, public_infrastructure_verify, readiness_payload, storage_diagnostic
from backend.worker_research import get_run, ingest_sources


def _extract_source_urls(question, explicit=()):
    return extract_source_urls(question, explicit)


def _bearer_token(request):
    return bearer_token(request)


def _authorized(request, env):
    return authorized(request, env)


async def _json(request):
    return await json_object(request)


async def _health_payload():
    return health_payload()


async def _readiness_payload(env):
    return await readiness_payload(env)


async def _storage_diagnostic(env, run_id):
    return await storage_diagnostic(env, run_id, persistence_cls=CloudflarePersistence)


async def _public_infrastructure_verify(env):
    return await public_infrastructure_verify(env, persistence_cls=CloudflarePersistence)


async def _ingest_sources(env, run_id, req):
    return await ingest_sources(env, run_id, req, fetcher=fetch_public_url, persistence_cls=CloudflarePersistence)


async def _get_run(env, run_id):
    return await get_run(env, run_id)


def _chat_headers(request):
    headers = {"Content-Type": "application/json"}
    token = _bearer_token(request)
    if token:
        headers["Authorization"] = f"Bearer {token}"
    idempotency_key = request.headers.get("Idempotency-Key")
    if idempotency_key:
        headers["Idempotency-Key"] = idempotency_key
    return headers


async def _operations_chat(env, payload, request):
    """Proxy synchronous Heroic AI chat through the configured private binding."""
    operations = getattr(env, "OPERATIONS", None)
    if operations is None:
        return {"ok": False, "error": "chat_backend_unavailable", "status": "unavailable"}, 503
    try:
        upstream = await operations.fetch(
            "https://chat/v1/chat",
            {"method": "POST", "headers": _chat_headers(request), "body": json.dumps(payload)},
        )
        body = await upstream.json()
        if not isinstance(body, dict):
            return {"ok": False, "error": "invalid_private_chat_response"}, 503
        return body, upstream.status
    except Exception:
        return {"ok": False, "error": "chat_backend_unavailable"}, 503


async def _operations_chat_stream(env, payload, request):
    """Proxy the private chatbot's SSE stream without exposing its topology."""
    operations = getattr(env, "OPERATIONS", None)
    if operations is None:
        return None, {"ok": False, "error": "chat_backend_unavailable", "status": "unavailable"}, 503
    try:
        upstream = await operations.fetch(
            "https://chat/v1/chat/stream",
            {"method": "POST", "headers": _chat_headers(request), "body": json.dumps(payload)},
        )
        return upstream, None, upstream.status
    except Exception:
        return None, {"ok": False, "error": "chat_backend_unavailable"}, 503


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
        upstream = await operations.fetch(
            "https://private/v1/dashboard",
            {"method": "GET", "headers": headers},
        )
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
            return Response.json(await _health_payload())

        if request.method == "GET" and path.endswith("/readiness"):
            payload, status = await _readiness_payload(self.env)
            return Response.json(payload, status=status)

        if request.method == "GET" and path.endswith("/api/v1/dashboard"):
            if not _authorized(request, self.env):
                return Response.json({"ok": False, "error": "unauthorized"}, status=401)
            body, status = await _operations_dashboard(self.env, request)
            return Response.json(body, status=status)

        if request.method == "POST" and path.endswith("/api/v1/chat/stream"):
            if not _authorized(request, self.env):
                return Response.json({"ok": False, "error": "unauthorized"}, status=401)
            payload = await _json(request)
            if payload is None:
                return Response.json({"ok": False, "error": "invalid JSON object"}, status=400)
            try:
                req = ChatRequest(**payload)
                req.validate()
            except (TypeError, ValueError) as exc:
                return Response.json({"ok": False, "error": str(exc)}, status=400)
            upstream, body, status = await _operations_chat_stream(self.env, payload, request)
            if upstream is not None:
                return upstream
            return Response.json(body, status=status)

        if request.method == "POST" and path.endswith("/api/v1/chat"):
            if not _authorized(request, self.env):
                return Response.json({"ok": False, "error": "unauthorized"}, status=401)
            payload = await _json(request)
            if payload is None:
                return Response.json({"ok": False, "error": "invalid JSON object"}, status=400)
            try:
                req = ChatRequest(**payload)
                req.validate()
            except (TypeError, ValueError) as exc:
                return Response.json({"ok": False, "error": str(exc)}, status=400)
            body, status = await _operations_chat(self.env, payload, request)
            return Response.json(body, status=status)

        if request.method == "POST" and path.endswith("/api/v1/chatbot/diagnostic"):
            if not _authorized(request, self.env):
                return Response.json({"ok": False, "error": "unauthorized"}, status=401)
            payload = await _json(request)
            if payload is None:
                return Response.json({"ok": False, "error": "invalid JSON object"}, status=400)
            if payload.get("operation") == "infrastructure_verify_public_test":
                body, status = await _public_infrastructure_verify(self.env)
                return Response.json(body, status=status)
            return Response.json({"ok": False, "error": "unsupported public diagnostic operation"}, status=400)

        if request.method == "POST" and path.endswith("/api/v1/storage/diagnostic"):
            if not _authorized(request, self.env):
                return Response.json({"ok": False, "error": "unauthorized"}, status=401)
            payload = await _json(request)
            if payload is None or not payload.get("run_id"):
                return Response.json({"ok": False, "error": "run_id is required"}, status=400)
            try:
                body, status = await _storage_diagnostic(self.env, str(payload["run_id"]))
                return Response.json(body, status=status)
            except Exception as exc:
                return Response.json({"ok": False, "error": f"storage diagnostic failure: {exc}"}, status=503)

        if request.method == "GET" and "/api/v1/research/" in path:
            if not _authorized(request, self.env):
                return Response.json({"ok": False, "error": "unauthorized"}, status=401)
            run_id = path.rsplit("/", 1)[-1]
            try:
                payload = await _get_run(self.env, run_id)
            except Exception as exc:
                return Response.json({"ok": False, "error": f"persistence failure: {exc}"}, status=503)
            if payload is None:
                return Response.json({"ok": False, "error": "run not found"}, status=404)
            return Response.json({"ok": True, **payload})

        if request.method == "POST" and path.endswith("/api/v1/research"):
            if not _authorized(request, self.env):
                return Response.json({"ok": False, "error": "unauthorized"}, status=401)
            payload = await _json(request)
            if payload is None:
                return Response.json({"ok": False, "error": "invalid JSON object"}, status=400)
            payload = dict(payload)
            question = str(payload.get("question") or "")
            payload["source_urls"] = list(_extract_source_urls(question, payload.get("source_urls") or ()))
            try:
                req = ResearchRequest(**payload)
            except TypeError as exc:
                return Response.json({"ok": False, "error": str(exc)}, status=400)
            result = submit_research(req)
            if not result.ok:
                return Response.json({"ok": False, "error": result.error}, status=400)

            persistence = CloudflarePersistence(self.env)
            idempotency_key = request.headers.get("Idempotency-Key")
            try:
                if idempotency_key:
                    run_id = await persistence.create_run_idempotent(req, idempotency_key)
                else:
                    run_id = result.run_id
                    await persistence.create_run(run_id, req)
                if not req.source_urls:
                    return Response.json({"ok": True, "run_id": run_id, "metadata": {**result.metadata, "execution_mode": "awaiting_source_urls", "source_url_ingestion": True, "general_web_discovery": False, "evidence_synthesis": False, "next_action": "provide one or more permitted public HTTP(S) source URLs"}, "sources": []})
                await persistence.set_run_status(run_id, "running")
                sources = await _ingest_sources(self.env, run_id, req)
                await persistence.set_run_status(run_id, "completed")
            except Exception as exc:
                try:
                    await persistence.set_run_status(run_id, "failed")
                except Exception:
                    pass
                return Response.json({"ok": False, "error": f"execution/persistence failure: {exc}"}, status=503)
            return Response.json({"ok": True, "run_id": run_id, "metadata": {**result.metadata, "execution_mode": "source_url_ingestion"}, "sources": sources})

        return Response.json({"ok": False, "error": "not found"}, status=404)
