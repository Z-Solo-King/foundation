from types import SimpleNamespace

import pytest

from backend.persistence.cloudflare import CloudflarePersistence, IDEMPOTENCY_CONTRACT_REVISION, IdempotencyConflictError
from backend.api.models import ResearchRequest


class FakeStatement:
    def __init__(self, value=None):
        self.value = value

    def bind(self, *args):
        return self

    async def first(self):
        return self.value


class FakeDB:
    def __init__(self, run=None):
        self.run = run
        self.batch_result = [SimpleNamespace(results=[]), SimpleNamespace(results=[]), SimpleNamespace(results=[])]

    def prepare(self, sql):
        if sql.startswith("SELECT * FROM research_runs"):
            return FakeStatement(self.run)
        return FakeStatement()

    async def batch(self, statements):
        return self.batch_result


class FakeArtifacts:
    async def put(self, key, content, **kwargs):
        return None

    async def get(self, key):
        return None

    async def delete(self, key):
        return None


def request():
    return ResearchRequest(
        question="coverage regression",
        depth="standard",
        require_citations=True,
        max_sources=2,
        max_evidence_items=4,
        strict_zero_cost_only=True,
        source_urls=(),
    )


def persistence(db, token=None):
    values = {"DB": db, "ARTIFACTS": FakeArtifacts()}
    if token is not None:
        values["AUTH_TOKEN"] = token
    return CloudflarePersistence(SimpleNamespace(**values))


@pytest.mark.asyncio
async def test_create_run_idempotent_rejects_oversized_key():
    with pytest.raises(ValueError, match="exceeds maximum length"):
        await persistence(FakeDB()).create_run_idempotent(request(), "x" * 257)


@pytest.mark.asyncio
async def test_set_run_status_rejects_missing_run():
    with pytest.raises(ValueError, match="not found"):
        await persistence(FakeDB()).set_run_status("missing", "running")


@pytest.mark.asyncio
async def test_set_run_status_rejects_invalid_stored_status():
    db = FakeDB({"run_id": "run-1", "status": "corrupt"})
    with pytest.raises(ValueError, match="stored run status is invalid"):
        await persistence(db).set_run_status("run-1", "running")


@pytest.mark.asyncio
async def test_set_run_status_rejects_disallowed_transition():
    db = FakeDB({"run_id": "run-1", "status": "completed"})
    with pytest.raises(ValueError, match="invalid run transition"):
        await persistence(db).set_run_status("run-1", "running")


@pytest.mark.asyncio
async def test_create_run_idempotent_binds_authenticated_scope():
    db = FakeDB()
    db.batch_result[2] = SimpleNamespace(results=[{
        "run_id": "run-scoped",
        "request_hash": "wrong",
        "subject_fingerprint": "other",
        "capability": "research",
        "contract_revision": IDEMPOTENCY_CONTRACT_REVISION,
    }])
    with pytest.raises(IdempotencyConflictError, match="execution scope"):
        await persistence(db, token="token-a").create_run_idempotent(request(), "same-key")


@pytest.mark.asyncio
async def test_create_run_idempotent_replays_same_scoped_request():
    p = persistence(FakeDB(), token="token-a")
    from backend.persistence.cloudflare import request_fingerprint, execution_scope_fingerprint
    scope = execution_scope_fingerprint(
        __import__("hashlib").sha256(b"token-a").hexdigest(), "research", IDEMPOTENCY_CONTRACT_REVISION
    )
    request_hash = __import__("hashlib").sha256(f"{request_fingerprint(request())}:{scope}".encode()).hexdigest()
    p.env.DB.batch_result[2] = SimpleNamespace(results=[{
        "run_id": "run-scoped",
        "request_hash": request_hash,
        "subject_fingerprint": __import__("hashlib").sha256(b"token-a").hexdigest(),
        "capability": "research",
        "contract_revision": IDEMPOTENCY_CONTRACT_REVISION,
    }])
    assert await p.create_run_idempotent(request(), "same-key") == "run-scoped"


@pytest.mark.asyncio
async def test_create_run_idempotent_uses_different_run_identity_for_different_subjects():
    from backend.persistence.cloudflare import execution_scope_fingerprint
    import hashlib
    a = execution_scope_fingerprint(hashlib.sha256(b"a").hexdigest(), "research", IDEMPOTENCY_CONTRACT_REVISION)
    b = execution_scope_fingerprint(hashlib.sha256(b"b").hexdigest(), "research", IDEMPOTENCY_CONTRACT_REVISION)
    assert a != b
