"""Cloudflare Python Worker entrypoint.

The Worker is a thin transport/persistence layer. Research policy and
protected promotion authority remain outside this public repository.
"""

import json
from datetime import datetime, timezone

from workers import Response, WorkerEntrypoint

from backend.api.models import ResearchRequest
from backend.api.main import health_endpoint, readiness_endpoint, submit_research


async def _json_request(request):
    try:
        return await request.json()
    except Exception:
        return None


async def _persist_run(env, run_id: str, request: ResearchRequest) -> None:
    if env.DB is None:
        return
    await env.DB.prepare(
        """INSERT INTO research_runs
           (run_id, question, depth, require_citations, max_sources,
            max_evidence_items, strict_zero_cost_only, status, created_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)"""
    ).bind(
        run_id,
        request.question,
        request.depth or "standard",
        1 if request.require_citations else 0,
        request.max_sources,
        request.max_evidence_items,
        1 if request.strict_zero_cost_only else 0,
        "planned",
        datetime.now(timezone.utc).isoformat(),
    ).run()


class Default(WorkerEntrypoint):
    async def fetch(self, request):
        url = request.url
        method = request.method.upper()

        if method == "GET" and url.endswith("/health"):
            return Response.json(health_endpoint())

        if method == "GET" and url.endswith("/readiness"):
            return Response.json(readiness_endpoint())

        if method == "POST" and url.endswith("/api/v1/research"):
            payload = await _json_request(request)
            if not isinstance(payload, dict):
                return Response.json({"ok": False, "error": "invalid JSON object"}, status=400)

            try:
                research_request = ResearchRequest(**payload)
            except TypeError as exc:
                return Response.json({"ok": False, "error": f"invalid request: {exc}"}, status=400)

            response = submit_research(research_request)
            if response.ok and response.run_id:
                try:
                    await _persist_run(self.env, response.run_id, research_request)
                except Exception as exc:
                    return Response.json(
                        {"ok": False, "error": f"persistence failure: {exc}"},
                        status=503,
                    )
            status = 200 if response.ok else 400
            return Response.json(json.loads(response_to_json(response)), status=status)

        return Response.json({"ok": False, "error": "not found"}, status=404)


def response_to_json(response) -> str:
    data = {"ok": response.ok}
    if response.error:
        data["error"] = response.error
    if response.run_id:
        data["run_id"] = response.run_id
    if response.metadata:
        data["metadata"] = response.metadata
    return json.dumps(data, default=str)
