"""Public Worker research ingestion and run retrieval."""
from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from urllib.parse import urlparse

from backend.models import ResearchRequest


async def ingest_sources(env, run_id, req, *, fetcher, persistence_cls):
    persistence = persistence_cls(env)
    results = []
    for index, url in enumerate(req.source_urls[:req.max_sources]):
        fetched = await fetcher(url)
        source_id = hashlib.sha256(fetched.final_url.encode()).hexdigest()[:32]
        content_hash = hashlib.sha256(fetched.content).hexdigest()
        version_id = hashlib.sha256((source_id + content_hash).encode()).hexdigest()[:32]
        observation_id = f"{run_id}:obs:{index}"
        family = urlparse(fetched.final_url).hostname or "unknown"
        now = datetime.now(timezone.utc).isoformat()
        access_state = "accessible" if 200 <= fetched.status < 400 else "error"
        await env.DB.prepare(
            """INSERT INTO sources
            (source_id, url, source_family_id, origin_kind, first_observed_at, last_observed_at, access_state)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(source_id) DO UPDATE SET
              url = excluded.url,
              source_family_id = excluded.source_family_id,
              last_observed_at = excluded.last_observed_at,
              access_state = excluded.access_state"""
        ).bind(source_id, fetched.final_url, family, "direct", now, now, access_state).run()
        artifact_ref = f"raw/{run_id}/{observation_id}/{content_hash}"
        await persistence.put_artifact(artifact_ref, fetched.content, content_type=fetched.content_type)
        await env.DB.prepare(
            """INSERT INTO document_versions
            (version_id, source_id, retrieved_at, etag, content_hash, artifact_ref, content_length)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(version_id) DO UPDATE SET
              source_id = excluded.source_id,
              retrieved_at = excluded.retrieved_at,
              etag = excluded.etag,
              artifact_ref = excluded.artifact_ref,
              content_length = excluded.content_length"""
        ).bind(version_id, source_id, now, fetched.etag, artifact_ref, len(fetched.content)).run()
        await env.DB.prepare(
            """INSERT INTO observations
            (observation_id, run_id, source_id, version_id, observed_at,
             retrieval_method, content_hash, integrity_state, access_state)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(observation_id) DO UPDATE SET
              source_id = excluded.source_id,
              version_id = excluded.version_id,
              observed_at = excluded.observed_at,
              retrieval_method = excluded.retrieval_method,
              content_hash = excluded.content_hash,
              integrity_state = excluded.integrity_state,
              access_state = excluded.access_state"""
        ).bind(observation_id, run_id, source_id, version_id, now, "http_fetch", content_hash, "verified", access_state).run()
        results.append({
            "url": fetched.final_url,
            "status": fetched.status,
            "source_id": source_id,
            "observation_id": observation_id,
            "version_id": version_id,
            "content_hash": content_hash,
            "bytes": len(fetched.content),
            "access_state": access_state,
            "retrieval_method": "http_fetch",
            "source_family_id": family,
        })
    return results


async def get_run(env, run_id):
    run = await env.DB.prepare("SELECT * FROM research_runs WHERE run_id = ?").bind(run_id).first()
    if not run:
        return None
    observations = await env.DB.prepare(
        """SELECT o.observation_id, o.source_id, o.version_id, o.observed_at,
                  o.retrieval_method, o.content_hash, o.integrity_state,
                  o.access_state, s.url, s.source_family_id
           FROM observations o JOIN sources s ON s.source_id = o.source_id
           WHERE o.run_id = ? ORDER BY o.observed_at ASC"""
    ).bind(run_id).all()
    run_status = run.get("status") if isinstance(run, dict) else getattr(run, "status", None)
    return {
        "run": run,
        "status": run_status or "unknown",
        "observations": observations,
        "result": None,
        "synthesis_available": False,
        "capabilities": {
            "source_url_ingestion": True,
            "general_web_discovery": False,
            "evidence_synthesis": False,
        },
    }
