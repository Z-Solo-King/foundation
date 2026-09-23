"""Public Worker readiness, storage and infrastructure diagnostics."""
from __future__ import annotations

import hashlib
import re
from datetime import datetime, timezone

from backend.api.main import health_endpoint, readiness_endpoint
from backend.api.models import ResearchRequest


def health_payload(env=None):
    payload = health_endpoint()
    environment = getattr(env, "ENVIRONMENT", None) if env is not None else None
    if env is not None:
        payload["environment"] = str(environment)
        foundation_sha = str(getattr(env, "RELEASE_FOUNDATION_SHA", "") or "").strip()
        operations_ref = str(getattr(env, "RELEASE_OPERATIONS_REF", "") or "").strip()
        if foundation_sha or operations_ref:
            payload["release"] = {
                "foundation_sha": foundation_sha or None,
                "operations_ref": operations_ref or None,
            }
    return payload


async def readiness_payload(env):
    # Release identity is part of readiness so external acceptance can verify immutable provenance.
    base = readiness_endpoint()
    database_ok = False
    try:
        row = await env.DB.prepare("SELECT 1 AS ok").first()
        database_ok = bool(row and row["ok"] == 1)
    except Exception:
        database_ok = False
    ready = base["ready"] and database_ok
    payload = {**base, "database": database_ok}
    foundation_sha = str(getattr(env, "RELEASE_FOUNDATION_SHA", "") or "").strip()
    operations_ref = str(getattr(env, "RELEASE_OPERATIONS_REF", "") or "").strip()
    if foundation_sha or operations_ref:
        payload["release"] = {
            "foundation_sha": foundation_sha or None,
            "operations_ref": operations_ref or None,
        }
    return payload, 200 if ready else 503


async def storage_diagnostic(env, run_id, *, persistence_cls):
    persistence = persistence_cls(env)
    rows = await env.DB.prepare(
        """SELECT d.artifact_ref, d.content_hash, d.content_length
           FROM document_versions d
           JOIN observations o ON o.version_id = d.version_id
           WHERE o.run_id = ? ORDER BY o.observed_at ASC"""
    ).bind(run_id).all()
    results = []
    for row in rows.results:
        key = row["artifact_ref"]
        content = await persistence.get_artifact(key)
        if content is None:
            results.append({"artifact_ref": key, "ok": False, "error": "artifact not found"})
            continue
        actual_hash = hashlib.sha256(bytes(content)).hexdigest()
        results.append({"artifact_ref": key, "ok": actual_hash == row["content_hash"] and len(content) == row["content_length"], "expected_sha256": row["content_hash"], "actual_sha256": actual_hash, "expected_bytes": row["content_length"], "actual_bytes": len(content)})
    ok = bool(results) and all(item["ok"] for item in results)
    return {"ok": ok, "run_id": run_id, "artifacts": results}, 200 if ok else 503


async def public_infrastructure_verify(env, *, persistence_cls):
    """Run bounded public D1/B2 lifecycle verification.

    The private chatbot binding is checked separately by the Worker route through
    the private diagnostic boundary; this helper intentionally has no private-binding dependency.
    """
    persistence = persistence_cls(env)
    checks = []
    run_id = "diag-" + hashlib.sha256(str(datetime.now(timezone.utc).timestamp()).encode()).hexdigest()[:24]
    try:
        row = await env.DB.prepare("SELECT 1 AS ok").first()
        if not row or row["ok"] != 1:
            raise RuntimeError("D1 health query failed")
        request = ResearchRequest(question="Public infrastructure self-test", depth="quick", require_citations=False, max_sources=1, max_evidence_items=1, strict_zero_cost_only=True, source_urls=[])
        await persistence.create_run(run_id, request)
        stored = await persistence.get_run(run_id)
        d1_ok = stored is not None
    except Exception:
        d1_ok = False
    checks.append({"name": "cloudflare_d1", "ok": d1_ok})
    key = f"diagnostics/chatbot/b2-lifecycle/{run_id}"
    content = b"research-intelligence-engine-b2-lifecycle"
    try:
        written = await persistence.put_artifact(key, content, content_type="text/plain")
        read_back = await persistence.get_artifact(key)
        await persistence.delete_artifact(key)
        deleted = await persistence.get_artifact(key)
        b2_ok = all((read_back == content, deleted is None, written["sha256"] == hashlib.sha256(content).hexdigest(), written["size"] == len(content)))
    except Exception as exc:
        b2_ok = False
        message = str(exc)
        match = re.search(r"B2 (?:PUT|GET|DELETE) failed \\((\\d{3})\\)", message)
        b2_error = f"b2_http_{match.group(1)}" if match else type(exc).__name__
    else:
        b2_error = None
    b2_check = {"name": "backblaze_b2_lifecycle", "ok": b2_ok}
    if b2_error:
        b2_check["error_class"] = b2_error
    checks.append(b2_check)
    ok = all(check["ok"] for check in checks)
    return {"ok": ok, "status": "ok" if ok else "degraded", "checks": checks}, 200 if ok else 503
