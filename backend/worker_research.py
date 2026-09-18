"""Public Worker research ingestion and run retrieval."""
from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from urllib.parse import urlparse

from backend.public_read_cursor import (
    DEFAULT_PUBLIC_READ_PAGE_SIZE,
    MAX_PUBLIC_READ_PAGE_SIZE,
    PUBLIC_READ_CURSOR_TTL_SECONDS,
    decode_cursor,
    encode_cursor,
)


async def ingest_sources(env, run_id, req, *, fetcher, persistence_cls):
    persistence = persistence_cls(env)
    results = []
    write_statements = []
    for index, url in enumerate(req.source_urls[:req.max_sources]):
        try:
            fetched = await fetcher(url)
            source_id = hashlib.sha256(fetched.final_url.encode()).hexdigest()[:32]
            content_hash = hashlib.sha256(fetched.content).hexdigest()
            version_id = hashlib.sha256((source_id + content_hash).encode()).hexdigest()[:32]
            observation_id = f"{run_id}:obs:{index}"
            family = urlparse(fetched.final_url).hostname or "unknown"
            now = datetime.now(timezone.utc).isoformat()
            access_state = "accessible" if 200 <= fetched.status < 400 else "error"
            write_statements.append(
                env.DB.prepare("""INSERT INTO sources (source_id, url, source_family_id, origin_kind, first_observed_at, last_observed_at, access_state) VALUES (?, ?, ?, ?, ?, ?, ?) ON CONFLICT(source_id) DO UPDATE SET url = excluded.url, source_family_id = excluded.source_family_id, last_observed_at = excluded.last_observed_at, access_state = excluded.access_state""").bind(
                    source_id, fetched.final_url, family, "direct", now, now, access_state
                )
            )
            artifact_ref = f"raw/{run_id}/{observation_id}/{content_hash}"
            await persistence.put_artifact(artifact_ref, fetched.content, content_type=fetched.content_type)
            write_statements.append(
                env.DB.prepare("""INSERT INTO document_versions (version_id, source_id, retrieved_at, etag, content_hash, artifact_ref, content_length) VALUES (?, ?, ?, ?, ?, ?, ?) ON CONFLICT(version_id) DO UPDATE SET source_id = excluded.source_id, retrieved_at = excluded.retrieved_at, etag = excluded.etag, artifact_ref = excluded.artifact_ref, content_length = excluded.content_length""").bind(
                    version_id, source_id, now, fetched.etag, content_hash, artifact_ref, len(fetched.content)
                )
            )
            write_statements.append(
                env.DB.prepare("""INSERT INTO observations (observation_id, run_id, source_id, version_id, observed_at, retrieval_method, content_hash, integrity_state, access_state) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?) ON CONFLICT(observation_id) DO UPDATE SET source_id = excluded.source_id, version_id = excluded.version_id, observed_at = excluded.observed_at, retrieval_method = excluded.retrieval_method, content_hash = excluded.content_hash, integrity_state = excluded.integrity_state, access_state = excluded.access_state""").bind(
                    observation_id, run_id, source_id, version_id, now, "http_fetch", content_hash, "verified", access_state
                )
            )
            results.append({"url": fetched.final_url, "status": fetched.status, "source_id": source_id, "observation_id": observation_id, "version_id": version_id, "content_hash": content_hash, "bytes": len(fetched.content), "access_state": access_state, "retrieval_method": "http_fetch", "source_family_id": family})
        except Exception as exc:
            results.append({"url": url, "status": "error", "error": str(exc)})
    if write_statements:
        await env.DB.batch(write_statements)
    return results


def _row_value(row, key, default=None):
    if isinstance(row, dict):
        return row.get(key, default)
    return getattr(row, key, default)


async def get_run(
    env,
    run_id,
    *,
    subject_fingerprint: str,
    cursor: str | None = None,
    limit: int = DEFAULT_PUBLIC_READ_PAGE_SIZE,
    cursor_secret: str,
):
    if not subject_fingerprint.strip() or not cursor_secret:
        raise ValueError("public read subject and cursor secret are required")
    if limit < 1 or limit > MAX_PUBLIC_READ_PAGE_SIZE:
        raise ValueError("public read page size is invalid")
    run = await env.DB.prepare(
        """SELECT run_id, status, created_at, updated_at, depth, require_citations,
        max_sources, max_evidence_items FROM research_runs
        WHERE run_id = ? AND subject_fingerprint = ?"""
    ).bind(run_id, subject_fingerprint).first()
    if not run:
        return None

    snapshot_id = str(_row_value(run, "updated_at") or _row_value(run, "created_at") or run_id)
    offset = 0
    if cursor:
        offset = decode_cursor(
            cursor,
            secret=cursor_secret,
            subject_fingerprint=subject_fingerprint,
            run_id=run_id,
            snapshot_id=snapshot_id,
        )

    rows = await env.DB.prepare(
        """SELECT o.observation_id, o.source_id, o.version_id, o.observed_at,
        o.retrieval_method, o.content_hash, o.integrity_state, o.access_state,
        s.url, s.source_family_id
        FROM observations o
        JOIN sources s ON s.source_id = o.source_id
        WHERE o.run_id = ?
        ORDER BY o.observed_at ASC, o.observation_id ASC
        LIMIT ? OFFSET ?"""
    ).bind(run_id, limit + 1, offset).all()
    if hasattr(rows, "results"):
        rows = rows.results
    items = list(rows or [])
    has_more = len(items) > limit
    items = items[:limit]
    public_run = {
        "run_id": _row_value(run, "run_id", run_id),
        "status": _row_value(run, "status", "unknown"),
        "created_at": _row_value(run, "created_at"),
        "updated_at": _row_value(run, "updated_at"),
        "depth": _row_value(run, "depth"),
        "require_citations": bool(_row_value(run, "require_citations", 0)),
        "max_sources": _row_value(run, "max_sources"),
        "max_evidence_items": _row_value(run, "max_evidence_items"),
    }
    next_cursor = None
    if has_more:
        next_cursor = encode_cursor(
            secret=cursor_secret,
            subject_fingerprint=subject_fingerprint,
            run_id=run_id,
            snapshot_id=snapshot_id,
            offset=offset + limit,
            expires_at=int(datetime.now(timezone.utc).timestamp()) + PUBLIC_READ_CURSOR_TTL_SECONDS,
        )
    return {
        "run": public_run,
        "status": public_run["status"],
        "observations": items,
        "result": None,
        "synthesis_available": False,
        "capabilities": {
            "source_url_ingestion": True,
            "general_web_discovery": False,
            "evidence_synthesis": False,
        },
        "pagination": {
            "limit": limit,
            "offset": offset,
            "has_more": has_more,
            "next_cursor": next_cursor,
            "snapshot_id": snapshot_id,
        },
    }
