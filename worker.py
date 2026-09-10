"""Cloudflare Python Worker entrypoint for the public-safe runtime."""

import hashlib
import hmac
from datetime import datetime, timezone
from urllib.parse import urlparse

from workers import Response, WorkerEntrypoint

from backend.api.main import health_endpoint, readiness_endpoint, submit_research
from backend.api.models import ResearchRequest
from backend.sources.http import fetch_public_url


def _bearer_token(request):
    value = request.headers.get("Authorization")
    if not value or not value.startswith("Bearer "):
        return None
    return value[7:].strip()


def _authorized(request, env):
    expected = getattr(env, "AUTH_TOKEN", None)
    environment = getattr(env, "ENVIRONMENT", "development")
    if environment != "production" and not expected:
        return True
    provided = _bearer_token(request)
    return bool(expected and provided and hmac.compare_digest(provided, expected))


async def _json(request):
    try:
        value = await request.json()
        return value if isinstance(value, dict) else None
    except Exception:
        return None


async def _persist_run(env, run_id, req):
    await env.DB.prepare(
        """INSERT INTO research_runs
        (run_id, question, depth, require_citations, max_sources,
         max_evidence_items, strict_zero_cost_only, status, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)"""
    ).bind(
        run_id, req.question, req.depth or "standard", int(req.require_citations),
        req.max_sources, req.max_evidence_items, int(req.strict_zero_cost_only),
        "planned", datetime.now(timezone.utc).isoformat()
    ).run()


async def _ingest_sources(env, run_id, req):
    results = []
    for index, url in enumerate(req.source_urls[:req.max_sources]):
        fetched = await fetch_public_url(url)
        source_id = hashlib.sha256(fetched.final_url.encode()).hexdigest()[:32]
        content_hash = hashlib.sha256(fetched.content).hexdigest()
        version_id = hashlib.sha256((source_id + content_hash).encode()).hexdigest()[:32]
        observation_id = f"{run_id}:obs:{index}"
        family = urlparse(fetched.final_url).hostname or "unknown"
        now = datetime.now(timezone.utc).isoformat()

        await env.DB.prepare(
            """INSERT OR IGNORE INTO sources
            (source_id, url, source_family_id, origin_kind, first_observed_at, last_observed_at, access_state)
            VALUES (?, ?, ?, ?, ?, ?, ?)"""
        ).bind(source_id, fetched.final_url, family, "direct", now, now,
               "accessible" if 200 <= fetched.status < 400 else "error").run()

        artifact_ref = f"raw/{run_id}/{observation_id}/{content_hash}"
        await env.ARTIFACTS.put(artifact_ref, fetched.content,
                                httpMetadata={"contentType": fetched.content_type})

        await env.DB.prepare(
            """INSERT OR REPLACE INTO document_versions
            (version_id, source_id, retrieved_at, etag, content_hash, artifact_ref, content_length)
            VALUES (?, ?, ?, ?, ?, ?, ?)"""
        ).bind(version_id, source_id, now, fetched.etag, content_hash,
               artifact_ref, len(fetched.content)).run()

        await env.DB.prepare(
            """INSERT OR REPLACE INTO observations
            (observation_id, run_id, source_id, version_id, observed_at,
             retrieval_method, content_hash, integrity_state, access_state)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)"""
        ).bind(observation_id, run_id, source_id, version_id, now, "http_fetch",
               content_hash, "verified", "accessible").run()

        results.append({
            "url": fetched.final_url,
            "status": fetched.status,
            "source_id": source_id,
            "observation_id": observation_id,
            "version_id": version_id,
            "content_hash": content_hash,
            "bytes": len(fetched.content),
        })
    return results


async def _control_plane_ready(env):
    control = getattr(env, "CONTROL_PLANE", None)
    if control is None:
        return False
    try:
        response = await control.fetch("https://control-plane/health")
        return response.status == 200
    except Exception:
        return False


class Default(WorkerEntrypoint):
    async def fetch(self, request):
        path = request.url.split("?", 1)[0]

        if request.method == "GET" and path.endswith("/health"):
            return Response.json(health_endpoint())

        if request.method == "GET" and path.endswith("/readiness"):
            base = readiness_endpoint()
            control_ready = await _control_plane_ready(self.env)
            ready = base["ready"] and control_ready
            return Response.json({**base, "control_plane": control_ready}, status=200 if ready else 503)

        if request.method == "POST" and path.endswith("/api/v1/research"):
            if not _authorized(request, self.env):
                return Response.json({"ok": False, "error": "unauthorized"}, status=401)
            payload = await _json(request)
            if payload is None:
                return Response.json({"ok": False, "error": "invalid JSON object"}, status=400)
            try:
                req = ResearchRequest(**payload)
            except TypeError as exc:
                return Response.json({"ok": False, "error": str(exc)}, status=400)
            result = submit_research(req)
            if not result.ok:
                return Response.json({"ok": False, "error": result.error}, status=400)
            try:
                await _persist_run(self.env, result.run_id, req)
                sources = await _ingest_sources(self.env, result.run_id, req) if req.source_urls else []
            except Exception as exc:
                return Response.json({"ok": False, "error": f"execution/persistence failure: {exc}"}, status=503)
            return Response.json({"ok": True, "run_id": result.run_id, "metadata": result.metadata, "sources": sources})

        return Response.json({"ok": False, "error": "not found"}, status=404)
