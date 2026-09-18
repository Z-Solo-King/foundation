"""Cloudflare Python Worker entrypoint for the standalone public-safe runtime."""
from __future__ import annotations

import json
import os
import uuid
from datetime import datetime, timezone
from urllib.parse import parse_qs, urlparse

from workers import Response, WorkerEntrypoint

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
from backend.worker_chat import _service_request, _chat_headers, _operations_chat, _operations_chat_stream, _operations_chatbot_diagnostic, _operations_dashboard



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




""Cloudflare Python Worker entrypoint for the standalone public-safe runtime."""
from __future__ import annotations

import json
import os
import uuid
from datetime import datetime, timezone
from urllib.parse import parse_qs, urlparse

from workers import Response, WorkerEntrypoint

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


