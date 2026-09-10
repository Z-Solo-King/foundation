"""Cloudflare Python Worker entrypoint for the public-safe runtime."""

import json
import uuid
from datetime import datetime, timezone

from workers import Response, WorkerEntrypoint

from backend.api.main import health_endpoint, readiness_endpoint, submit_research
from backend.api.models import ResearchRequest


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


class Default(WorkerEntrypoint):
    async def fetch(self, request):
        if request.method == "GET" and request.url.endswith("/health"):
            return Response.json(health_endpoint())
        if request.method == "GET" and request.url.endswith("/readiness"):
            return Response.json(readiness_endpoint())
        if request.method == "POST" and request.url.endswith("/api/v1/research"):
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
            return Response.json({
                "ok": True,
                "run_id": result.run_id,
                "metadata": result.metadata,
            })
        return Response.json({"ok": False, "error": "not found"}, status=404)
