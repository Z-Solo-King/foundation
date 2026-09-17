"""Concrete D1 and provider-neutral artifact persistence for Cloudflare Workers."""

from datetime import datetime, timezone
import hashlib
import json

from backend.persistence.artifacts import artifact_store_from_env

IDEMPOTENCY_CONTRACT_REVISION = "research-idempotency/v2"


class IdempotencyConflictError(RuntimeError):
    """Raised when an idempotency key is reused outside its execution scope."""


_ALLOWED_TRANSITIONS = {
    "planned": frozenset({"planned", "running", "failed"}),
    "running": frozenset({"running", "completed", "failed"}),
    "completed": frozenset({"completed"}),
    "failed": frozenset({"failed", "running"}),
}


def request_fingerprint(request) -> str:
    payload = {
        "question": request.question,
        "depth": request.depth or "standard",
        "require_citations": bool(request.require_citations),
        "max_sources": request.max_sources,
        "max_evidence_items": request.max_evidence_items,
        "strict_zero_cost_only": bool(request.strict_zero_cost_only),
        "source_urls": list(request.source_urls),
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode()).hexdigest()


def execution_scope_fingerprint(subject_fingerprint: str, capability: str, contract_revision: str) -> str:
    scope = {
        "subject_fingerprint": subject_fingerprint,
        "capability": capability,
        "contract_revision": contract_revision,
    }
    encoded = json.dumps(scope, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode()).hexdigest()


class CloudflarePersistence:
    def __init__(self, env):
        self.env = env
        self.artifacts = getattr(env, "ARTIFACTS", None) or artifact_store_from_env(env)

    async def create_run(self, run_id, request):
        now = datetime.now(timezone.utc).isoformat()
        await self.env.DB.prepare(
            """INSERT INTO research_runs
            (run_id, question, depth, require_citations, max_sources,
             max_evidence_items, strict_zero_cost_only, status, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"""
        ).bind(
            run_id,
            request.question,
            request.depth or "standard",
            int(request.require_citations),
            request.max_sources,
            request.max_evidence_items,
            int(request.strict_zero_cost_only),
            "planned",
            now,
            now,
        ).run()
        return run_id

    async def create_run_idempotent(
        self,
        request,
        idempotency_key: str,
        subject_fingerprint: str | None = None,
        capability: str = "research",
        contract_revision: str | None = None,
    ):
        """Atomically claim an idempotency key within an authenticated execution scope."""
        if not idempotency_key or not idempotency_key.strip():
            raise ValueError("idempotency_key must not be empty")
        if len(idempotency_key) > 256:
            raise ValueError("idempotency_key exceeds maximum length")

        legacy_mode = subject_fingerprint is None and not getattr(self.env, "AUTH_TOKEN", None)
        if subject_fingerprint is None:
            auth_token = getattr(self.env, "AUTH_TOKEN", None)
            subject_fingerprint = hashlib.sha256(str(auth_token).encode()).hexdigest() if auth_token else "legacy"
        contract_revision = contract_revision or (
            "v1" if legacy_mode else IDEMPOTENCY_CONTRACT_REVISION
        )
        if not isinstance(subject_fingerprint, str) or not subject_fingerprint.strip():
            raise ValueError("subject_fingerprint must not be empty")
        if not isinstance(capability, str) or not capability.strip():
            raise ValueError("capability must not be empty")
        if not isinstance(contract_revision, str) or not contract_revision.strip():
            raise ValueError("contract_revision must not be empty")

        if legacy_mode:
            scope_fingerprint = execution_scope_fingerprint("legacy", "research", "v1")
            request_hash = request_fingerprint(request)
            run_id = f"run-{hashlib.sha256(idempotency_key.encode()).hexdigest()[:32]}"
        else:
            scope_fingerprint = execution_scope_fingerprint(
                subject_fingerprint, capability, contract_revision
            )
            request_hash = hashlib.sha256(
                f"{request_fingerprint(request)}:{scope_fingerprint}".encode()
            ).hexdigest()
            run_id = f"run-{hashlib.sha256(f'{scope_fingerprint}:{idempotency_key}'.encode()).hexdigest()[:32]}"

        now = datetime.now(timezone.utc).isoformat()
        claim = self.env.DB.prepare(
            """INSERT INTO idempotency_keys
            (idempotency_key, run_id, request_hash, created_at,
             subject_fingerprint, capability, contract_revision)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(idempotency_key) DO NOTHING"""
        ).bind(
            idempotency_key,
            run_id,
            request_hash,
            now,
            subject_fingerprint,
            capability,
            contract_revision,
        )
        create = self.env.DB.prepare(
            """INSERT INTO research_runs
            (run_id, question, depth, require_citations, max_sources,
             max_evidence_items, strict_zero_cost_only, status, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(run_id) DO NOTHING"""
        ).bind(
            run_id,
            request.question,
            request.depth or "standard",
            int(request.require_citations),
            request.max_sources,
            request.max_evidence_items,
            int(request.strict_zero_cost_only),
            "planned",
            now,
            now,
        )
        lookup = self.env.DB.prepare(
            """SELECT run_id, request_hash, subject_fingerprint,
             capability, contract_revision
             FROM idempotency_keys WHERE idempotency_key = ?"""
        ).bind(idempotency_key)

        result = await self.env.DB.batch([claim, create, lookup])
        row = result[2].results[0] if result[2].results else None
        if row is None:
            raise RuntimeError("idempotency claim was not persisted")

        if legacy_mode:
            if row["request_hash"] != request_hash:
                raise IdempotencyConflictError(
                    "idempotency key was already used for a different request"
                )
        else:
            if isinstance(row, dict):
                stored_hash = row.get("request_hash")
                stored_scope = (
                    row.get("subject_fingerprint", "legacy"),
                    row.get("capability", "research"),
                    row.get("contract_revision", "v1"),
                )
            else:
                stored_hash = row[1]
                stored_scope = (row[2], row[3], row[4])
            if stored_hash != request_hash or stored_scope != (
                subject_fingerprint,
                capability,
                contract_revision,
            ):
                raise IdempotencyConflictError(
                    "idempotency key was already used outside its execution scope"
                )
        return row["run_id"] if isinstance(row, dict) else row[0]

    async def get_run(self, run_id):
        return await self.env.DB.prepare(
            "SELECT * FROM research_runs WHERE run_id = ?"
        ).bind(run_id).first()

    async def set_run_status(self, run_id, status):
        if status not in _ALLOWED_TRANSITIONS:
            raise ValueError("invalid run status")
        current = await self.get_run(run_id)
        if not current:
            raise ValueError(f"run {run_id} not found")
        current_status = current.get("status") if isinstance(current, dict) else getattr(current, "status", None)
        if current_status not in _ALLOWED_TRANSITIONS:
            raise ValueError("stored run status is invalid")
        if status not in _ALLOWED_TRANSITIONS[current_status]:
            raise ValueError(f"invalid run transition: {current_status} -> {status}")
        await self.env.DB.prepare(
            "UPDATE research_runs SET status = ?, updated_at = ? WHERE run_id = ?"
        ).bind(status, datetime.now(timezone.utc).isoformat(), run_id).run()

    async def put_artifact(self, key, content, content_type="application/octet-stream"):
        digest = hashlib.sha256(content).hexdigest()
        await self.artifacts.put(key, content, content_type=content_type)
        return {"key": key, "sha256": digest, "size": len(content)}

    async def get_artifact(self, key):
        value = await self.artifacts.get(key)
        if value is None or isinstance(value, (bytes, bytearray, memoryview)):
            return bytes(value) if value is not None else None
        body = getattr(value, "body", None)
        array_buffer = getattr(body, "arrayBuffer", None)
        if callable(array_buffer):
            return bytes(await array_buffer())
        return value

    async def delete_artifact(self, key):
        await self.artifacts.delete(key)
