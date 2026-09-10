"""Production Cloudflare D1/R2 adapters used by the Python Worker.

The in-memory repositories remain useful for deterministic local tests; this
module supplies the actual Workers bindings used in deployment.
"""

from datetime import datetime, timezone
import hashlib
import json


class CloudflarePersistence:
    def __init__(self, env):
        self.env = env

    async def record_run(self, run_id: str, question: str, depth: str, require_citations: bool,
                         max_sources: int, max_evidence_items: int, strict_zero_cost_only: bool) -> None:
        await self.env.DB.prepare(
            """INSERT INTO research_runs
               (run_id, question, depth, require_citations, max_sources,
                max_evidence_items, strict_zero_cost_only, status, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)"""
        ).bind(
            run_id,
            question,
            depth,
            1 if require_citations else 0,
            max_sources,
            max_evidence_items,
            1 if strict_zero_cost_only else 0,
            "planned",
            datetime.now(timezone.utc).isoformat(),
        ).run()

    async def get_run(self, run_id: str):
        result = await self.env.DB.prepare(
            "SELECT * FROM research_runs WHERE run_id = ?"
        ).bind(run_id).first()
        return result

    async def update_run_status(self, run_id: str, status: str) -> None:
        allowed = {"planned", "running", "completed", "failed"}
        if status not in allowed:
            raise ValueError("invalid run status")
        await self.env.DB.prepare(
            "UPDATE research_runs SET status = ? WHERE run_id = ?"
        ).bind(status, run_id).run()

    async def put_artifact(self, key: str, content: bytes, content_type: str = "application/octet-stream") -> dict[str, object]:
        digest = hashlib.sha256(content).hexdigest()
        await self.env.ARTIFACTS.put(key, content, httpMetadata={"contentType": content_type})
        return {"key": key, "sha256": digest, "size": len(content)}

    async def get_artifact(self, key: str) -> bytes | None:
        obj = await self.env.ARTIFACTS.get(key)
        if obj is None:
            return None
        return await obj.body.arrayBuffer()
