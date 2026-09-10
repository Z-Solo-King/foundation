"""Cloudflare Python Worker entrypoint for the public-safe runtime."""

import hmac
from datetime import datetime, timezone

from workers import Response, WorkerEntrypoint

from backend.api.main import health_endpoint, readiness_endpoint, submit_research
from backend.api.models import ResearchRequest


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


async def _persist(env, run_id, req):
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
            if not base["ready"]:
                return Response.json({**base, "control_plane": False}, status=503)
            control_ready = await _control_plane_ready(self.env)
            return Response.json({**base, "control_plane": control_ready}, status=200 if control_ready else 503)

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
                await _persist(self.env, result.run_id, req)
            except Exception as exc:
                return Response.json({"ok": False, "error": f"persistence failure: {exc}"}, status=503)
            return Response.json({"ok": True, "run_id": result.run_id, "metadata": result.metadata})

        return Response.json({"ok": False, "error": "not found"}, status=404)
