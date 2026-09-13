"""Cloudflare Python Worker entrypoint for the public-safe runtime."""

import hashlib
import hmac
import json
from datetime import datetime, timezone
from urllib.parse import urlparse

from workers import Response, WorkerEntrypoint

from backend.api.main import submit_research
from backend.api.models import ResearchRequest
from backend.persistence.cloudflare import CloudflarePersistence
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


async def _health_payload():
    from backend.api.main import health_endpoint

    return health_endpoint()


async def _readiness_payload(env):
    from backend.api.main import readiness_endpoint

    base = readiness_endpoint()
    control_ready = await _control_plane_ready(env)
    ready = base["ready"] and control_ready
    return {**base, "control_plane": control_ready}, 200 if ready else 503


async def _control_plane_ready(env):
    control = getattr(env, "CONTROL_PLANE", None)
    if control is None:
        return False
    try:
        response = await control.fetch("https://control-plane/health")
        return response.status == 200
    except Exception:
        return False


async def _control_plane_chatbot_diagnostic(env, payload):
    control = getattr(env, "CONTROL_PLANE", None)
    if control is None:
        return {"ok": False, "error": "control plane service binding is unavailable"}, 503
    try:
        operation = str(payload.get("operation", ""))
        path = "/v1/diagnostics/infrastructure" if operation == "infrastructure_verify" else "/v1/diagnostics/chatbot"
        response = await control.fetch(
            f"https://control-plane{path}",
            {"method": "POST", "headers": {"Content-Type": "application/json"}, "body": json.dumps(payload)},
        )
        body = await response.json()
        return body, response.status
    except Exception as exc:
        return {"ok": False, "error": f"control plane diagnostic failure: {exc}"}, 503


async def _storage_diagnostic(env, run_id):
    persistence = CloudflarePersistence(env)
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
        results.append({
            "artifact_ref": key,
            "ok": actual_hash == row["content_hash"] and len(content) == row["content_length"],
            "expected_sha256": row["content_hash"],
            "actual_sha256": actual_hash,
            "expected_bytes": row["content_length"],
            "actual_bytes": len(content),
        })
    ok = bool(results) and all(item["ok"] for item in results)
    return {"ok": ok, "run_id": run_id, "artifacts": results}, 200 if ok else 503


async def _public_infrastructure_verify(env):
    """Run the live Cloudflare/D1/B2 test without consuming private Worker quota."""
    persistence = CloudflarePersistence(env)
    checks = [{"name": "public_chatbot", "ok": True}]

    try:
        await env.DB.prepare("SELECT 1 AS ok").first()
        request = ResearchRequest(
            question="Public chatbot infrastructure self-test",
            depth="quick",
            require_citations=False,
            max_sources=0,
            max_evidence_items=1,
            strict_zero_cost_only=True,
            source_urls=[],
        )
        run_id = "diag-" + hashlib.sha256(str(datetime.now(timezone.utc).timestamp()).encode()).hexdigest()[:24]
        await persistence.create_run(run_id, request)
        stored = await persistence.get_run(run_id)
        d1_ok = stored is not None
    except Exception:
        d1_ok = False
    checks.append({"name": "cloudflare_d1", "ok": d1_ok})

    key = "diagnostics/chatbot/b2-lifecycle"
    content = b"research-intelligence-engine-b2-lifecycle"
    try:
        written = await persistence.put_artifact(key, content, content_type="text/plain")
        read_back = await persistence.get_artifact(key)
        await persistence.delete_artifact(key)
        deleted = await persistence.get_artifact(key)
        b2_ok = all((
            read_back == content,
            deleted is None,
            written["sha256"] == hashlib.sha256(content).hexdigest(),
            written["size"] == len(content),
        ))
    except Exception:
        b2_ok = False
    checks.append({"name": "backblaze_b2_lifecycle", "ok": b2_ok})

    ok = all(check["ok"] for check in checks)
    return {"ok": ok, "status": "ok" if ok else "degraded", "checks": checks}, 200 if ok else 503


async def _ingest_sources(env, run_id, req):
    persistence = CloudflarePersistence(env)
    results = []
    for index, url in enumerate(req.source_urls[:req.max_sources]):
        fetched = await fetch_public_url(url)
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
        ).bind(version_id, source_id, now, fetched.etag, content_hash, artifact_ref, len(fetched.content)).run()

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

        results.append({"url": fetched.final_url, "status": fetched.status, "source_id": source_id, "observation_id": observation_id, "version_id": version_id, "content_hash": content_hash, "bytes": len(fetched.content)})
    return results


async def _get_run(env, run_id):
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
    return {"run": run, "observations": observations}


class Default(WorkerEntrypoint):
    async def fetch(self, request):
        path = request.url.split("?", 1)[0]

        if request.method == "GET" and path.endswith("/health"):
            return Response.json(await _health_payload())

        if request.method == "GET" and path.endswith("/readiness"):
            payload, status = await _readiness_payload(self.env)
            return Response.json(payload, status=status)

        if request.method == "POST" and path.endswith("/api/v1/chatbot/diagnostic"):
            if not _authorized(request, self.env):
                return Response.json({"ok": False, "error": "unauthorized"}, status=401)
            payload = await _json(request)
            if payload is None:
                return Response.json({"ok": False, "error": "invalid JSON object"}, status=400)
            if payload.get("operation") == "infrastructure_verify_public_test":
                body, status = await _public_infrastructure_verify(self.env)
                return Response.json(body, status=status)
            body, status = await _control_plane_chatbot_diagnostic(self.env, payload)
            return Response.json(body, status=status)

        if request.method == "POST" and path.endswith("/api/v1/storage/diagnostic"):
            if not _authorized(request, self.env):
                return Response.json({"ok": False, "error": "unauthorized"}, status=401)
            payload = await _json(request)
            if payload is None or not payload.get("run_id"):
                return Response.json({"ok": False, "error": "run_id is required"}, status=400)
            try:
                body, status = await _storage_diagnostic(self.env, str(payload["run_id"]))
                return Response.json(body, status=status)
            except Exception as exc:
                return Response.json({"ok": False, "error": f"storage diagnostic failure: {exc}"}, status=503)

        if request.method == "GET" and "/api/v1/research/" in path:
            if not _authorized(request, self.env):
                return Response.json({"ok": False, "error": "unauthorized"}, status=401)
            run_id = path.rsplit("/", 1)[-1]
            try:
                payload = await _get_run(self.env, run_id)
            except Exception as exc:
                return Response.json({"ok": False, "error": f"persistence failure: {exc}"}, status=503)
            if payload is None:
                return Response.json({"ok": False, "error": "run not found"}, status=404)
            return Response.json({"ok": True, **payload})

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

            persistence = CloudflarePersistence(self.env)
            idempotency_key = request.headers.get("Idempotency-Key")
            try:
                if idempotency_key:
                    run_id = await persistence.create_run_idempotent(req, idempotency_key)
                else:
                    run_id = result.run_id
                    await persistence.create_run(run_id, req)
                sources = await _ingest_sources(self.env, run_id, req) if req.source_urls else []
            except Exception as exc:
                return Response.json({"ok": False, "error": f"execution/persistence failure: {exc}"}, status=503)
            return Response.json({"ok": True, "run_id": run_id, "metadata": result.metadata, "sources": sources})

        return Response.json({"ok": False, "error": "not found"}, status=404)
