from types import SimpleNamespace
import hashlib

import pytest

from backend.persistence.cloudflare import (
    CloudflarePersistence,
    IDEMPOTENCY_CONTRACT_REVISION,
    IdempotencyConflictError,
    execution_scope_fingerprint,
    request_fingerprint,
)
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
    subject = hashlib.sha256(b"token-a").hexdigest()
    scope = execution_scope_fingerprint(subject, "research", IDEMPOTENCY_CONTRACT_REVISION)
    request_hash = hashlib.sha256(f"{request_fingerprint(request())}:{scope}".encode()).hexdigest()
    p = persistence(FakeDB(), token="token-a")
    p.env.DB.batch_result[2] = SimpleNamespace(results=[{
        "run_id": "run-scoped",
        "request_hash": request_hash,
        "subject_fingerprint": subject,
        "capability": "research",
        "contract_revision": IDEMPOTENCY_CONTRACT_REVISION,
    }])
    assert await p.create_run_idempotent(request(), "same-key") == "run-scoped"


@pytest.mark.asyncio
async def test_create_run_idempotent_uses_different_run_identity_for_different_subjects():
    a = execution_scope_fingerprint(hashlib.sha256(b"a").hexdigest(), "research", IDEMPOTENCY_CONTRACT_REVISION)
    b = execution_scope_fingerprint(hashlib.sha256(b"b").hexdigest(), "research", IDEMPOTENCY_CONTRACT_REVISION)
    assert a != b


@pytest.mark.asyncio
async def test_create_run_idempotent_accepts_explicit_scope():
    p = persistence(FakeDB())
    subject = "subject-a"
    p.env.DB.batch_result[2] = SimpleNamespace(results=[{
        "run_id": "run-explicit",
        "request_hash": "ignored",
        "subject_fingerprint": subject,
        "capability": "chat",
        "contract_revision": "chat/v3",
    }])
    assert await p.create_run_idempotent(
        request(), "explicit-key", subject_fingerprint=subject, capability="chat", contract_revision="chat/v3"
    ) == "run-explicit"


@pytest.mark.asyncio
async def test_create_run_idempotent_rejects_empty_scope_values():
    cases = (
        {"subject_fingerprint": "   "},
        {"capability": ""},
        {"contract_revision": "   "},
    )
    for kwargs in cases:
        with pytest.raises(ValueError):
            await persistence(FakeDB()).create_run_idempotent(request(), "scope-key", **kwargs)


@pytest.mark.asyncio
async def test_create_run_idempotent_rejects_missing_claim_row():
    with pytest.raises(RuntimeError, match="claim was not persisted"):
        await persistence(FakeDB(), token="token-a").create_run_idempotent(request(), "missing-row")


@pytest.mark.asyncio
async def test_create_run_idempotent_rejects_legacy_request_conflict():
    db = FakeDB()
    db.batch_result[2] = SimpleNamespace(results=[{
        "run_id": "run-existing",
        "request_hash": "different",
    }])
    with pytest.raises(IdempotencyConflictError, match="different request"):
        await persistence(db).create_run_idempotent(request(), "legacy-key")


@pytest.mark.asyncio
async def test_create_run_idempotent_rejects_scoped_request_hash_conflict():
    db = FakeDB()
    db.batch_result[2] = SimpleNamespace(results=[{
        "run_id": "run-existing",
        "request_hash": "different",
        "subject_fingerprint": "subject-a",
        "capability": "research",
        "contract_revision": IDEMPOTENCY_CONTRACT_REVISION,
    }])
    with pytest.raises(IdempotencyConflictError, match="execution scope"):
        await persistence(db, token="token-a").create_run_idempotent(request(), "scoped-key")


@pytest.mark.asyncio
async def test_create_run_idempotent_rejects_scoped_identity_mismatch_with_matching_hash():
    subject = hashlib.sha256(b"token-a").hexdigest()
    scope = execution_scope_fingerprint(subject, "research", IDEMPOTENCY_CONTRACT_REVISION)
    request_hash = hashlib.sha256(f"{request_fingerprint(request())}:{scope}".encode()).hexdigest()
    db = FakeDB()
    db.batch_result[2] = SimpleNamespace(results=[{
        "run_id": "run-existing",
        "request_hash": request_hash,
        "subject_fingerprint": subject,
        "capability": "other-capability",
        "contract_revision": IDEMPOTENCY_CONTRACT_REVISION,
    }])
    with pytest.raises(IdempotencyConflictError, match="execution scope"):
        await persistence(db, token="token-a").create_run_idempotent(request(), "scope-mismatch")


@pytest.mark.asyncio
async def test_create_run_idempotent_supports_non_dict_database_rows():
    subject = hashlib.sha256(b"token-a").hexdigest()
    scope = execution_scope_fingerprint(subject, "research", IDEMPOTENCY_CONTRACT_REVISION)
    request_hash = hashlib.sha256(f"{request_fingerprint(request())}:{scope}".encode()).hexdigest()
    row = ("run-tuple", request_hash, subject, "research", IDEMPOTENCY_CONTRACT_REVISION)
    db = FakeDB()
    db.batch_result[2] = SimpleNamespace(results=[row])
    assert await persistence(db, token="token-a").create_run_idempotent(request(), "tuple-key") == "run-tuple"
