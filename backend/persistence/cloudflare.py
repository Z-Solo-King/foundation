"""Concrete D1/R2 adapters for Cloudflare Python Workers."""

from datetime import datetime, timezone
import hashlib


class CloudflarePersistence:
    def __init__(self, env):
        self.env = env

    async def create_run(self, run_id, request):
        await self.env.DB.prepare(
            """INSERT INTO research_runs
            (run_id, question, depth, require_citations, max_sources,
             max_evidence_items, strict_zero_cost_only, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)"""
        ).bind(
            run_id, request.question, request.depth or "standard",
            int(request.require_citations), request.max_sources,
            request.max_evidence_items, int(request.strict_zero_cost_only),
            "planned", datetime.now(timezone.utc).isoformat()
        ).run()

    async def get_run(self, run_id):
        return await self.env.DB.prepare(
            "SELECT * FROM research_runs WHERE run_id = ?"
        ).bind(run_id).first()

    async def set_run_status(self, run_id, status):
        if status not in {"planned", "running", "completed", "failed"}:
            raise ValueError("invalid run status")
        await self.env.DB.prepare(
            "UPDATE research_runs SET status = ? WHERE run_id = ?"
        ).bind(status, run_id).run()

    async def put_artifact(self, key, content, content_type="application/octet-stream"):
        digest = hashlib.sha256(content).hexdigest()
        await self.env.ARTIFACTS.put(
            key, content, httpMetadata={"contentType": content_type}
        )
        return {"key": key, "sha256": digest, "size": len(content)}

    async def get_artifact(self, key):
        obj = await self.env.ARTIFACTS.get(key)
        if obj is None:
            return None
        return await obj.body.arrayBuffer()
