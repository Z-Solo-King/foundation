from types import SimpleNamespace

import pytest

import worker


class Statement:
    def __init__(self, value=None):
        self.value = value
        self.bound = ()

    def bind(self, *args):
        self.bound = args
        return self

    async def first(self):
        return self.value

    async def all(self):
        return self.value or []

    async def run(self):
        return {"success": True, "meta": {"last_row_id": 7}}


class DB:
    def __init__(self):
        self.statements = []

    def prepare(self, sql):
        self.statements.append(sql)
        if sql.startswith("SELECT run_id FROM research_runs"):
            return Statement({"run_id": "run-1"})
        if sql.startswith("SELECT observation_id FROM observations"):
            return Statement([])
        return Statement()


@pytest.mark.asyncio
async def test_publish_evidence_appends_without_conflict_update(monkeypatch):
    package = {"run_id": "run-1", "claims": []}
    db = DB()
    env = SimpleNamespace(DB=db, EVIDENCE_PACKAGE_SIGNING_SECRET="secret")
    monkeypatch.setattr(worker, "verify_package", lambda *args, **kwargs: (True, None))
    monkeypatch.setattr(worker, "package_digest", lambda value: "digest-1")

    body, status = await worker._publish_evidence(env, "run-1", package)

    assert status == 200
    assert body["publication_id"] == 7
    insert = next(sql for sql in db.statements if sql.startswith("INSERT INTO research_publications"))
    assert "ON CONFLICT" not in insert


@pytest.mark.asyncio
async def test_publish_evidence_preserves_distinct_publications(monkeypatch):
    package = {"run_id": "run-1", "claims": []}
    db = DB()
    env = SimpleNamespace(DB=db, EVIDENCE_PACKAGE_SIGNING_SECRET="secret")
    monkeypatch.setattr(worker, "verify_package", lambda *args, **kwargs: (True, None))
    digests = iter(("digest-1", "digest-2"))
    monkeypatch.setattr(worker, "package_digest", lambda value: next(digests))

    first, _ = await worker._publish_evidence(env, "run-1", package)
    second, _ = await worker._publish_evidence(env, "run-1", package)

    assert first["package_digest"] != second["package_digest"]
    assert first["publication_id"] == second["publication_id"] == 7
    assert sum(sql.startswith("INSERT INTO research_publications") for sql in db.statements) == 2
