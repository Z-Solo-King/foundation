
async def _claim_idempotent_run(env, request, idempotency_key, subject_fingerprint, capability, contract_revision, request_hash, run_id, legacy_mode):
    now = datetime.now(timezone.utc).isoformat()
    claim = env.DB.prepare(
        """INSERT INTO idempotency_keys
        (idempotency_key, run_id, request_hash, created_at,
         subject_fingerprint, capability, contract_revision)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(idempotency_key) DO NOTHING"""
    ).bind(idempotency_key, run_id, request_hash, now, subject_fingerprint, capability, contract_revision)
    create = env.DB.prepare(
        """INSERT INTO research_runs
        (run_id, subject_fingerprint, question, depth, require_citations, max_sources,
         max_evidence_items, strict_zero_cost_only, status, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(run_id) DO NOTHING"""
    ).bind(
        run_id, subject_fingerprint, request.question, request.depth or "standard", int(request.require_citations),
        request.max_sources, request.max_evidence_items, int(request.strict_zero_cost_only),
        "planned", now, now,
    )
    # Cloudflare Python Workers D1 reliably supports the serial prepare/bind/run/first
    # pattern used by the chat idempotency authority. Keep the INSERT ... DO NOTHING
    # semantics for concurrency, but avoid mixing INSERT and SELECT in a D1 batch.
    await claim.run()
    await create.run()
    row = await env.DB.prepare(
        """SELECT run_id, request_hash, subject_fingerprint,
        capability, contract_revision FROM idempotency_keys
        WHERE idempotency_key = ?"""
    ).bind(idempotency_key).first()
    if row is None:
        raise RuntimeError("idempotency claim was not persisted")
    if isinstance(row, dict):
        stored_hash = row.get("request_hash")
        stored_scope = (
            row.get("subject_fingerprint", "legacy"),
            row.get("capability", "research"),
            row.get("contract_revision", "v1"),
        )
        stored_run_id = row.get("run_id")
    else:
        stored_hash = row[1]
        stored_scope = (row[2], row[3], row[4])
        stored_run_id = row[0]
    if legacy_mode:
        if stored_hash != request_hash:
            raise IdempotencyConflictError("idempotency key was already used for a different request")
    elif stored_hash != request_hash or stored_scope != (subject_fingerprint, capability, contract_revision):
        raise IdempotencyConflictError("idempotency key was already used outside its execution scope")
    return stored_run_id


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