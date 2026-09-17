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


class NonDictStatement(Statement):
    async def run(self):
        return None


class DB:
    def __init__(self, non_dict_insert=False):
        self.statements = []
        self.non_dict_insert = non_dict_insert

    def prepare(self, sql):
        self.statements.append(sql)
        if sql.startswith("SELECT run_id FROM research_runs"):
            return Statement({"run_id": "run-1"})
        if sql.startswith("SELECT observation_id FROM observations"):
            return Statement([])
        return NonDictStatement() if self.non_dict_insert else Statement()


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
async def test_publish_evidence_allows_multiple_inserts_for_one_run(monkeypatch):
    package = {"run_id": "run-1", "claims": []}
    db = DB()
    env = SimpleNamespace(DB=db, EVIDENCE_PACKAGE_SIGNING_SECRET="secret")
    monkeypatch.setattr(worker, "verify_package", lambda *args, **kwargs: (True, None))
    digests = iter(("digest-1", "digest-2"))
    monkeypatch.setattr(worker, "package_digest", lambda value: next(digests))

    first, _ = await worker._publish_evidence(env, "run-1", package)
    second, _ = await worker._publish_evidence(env, "run-1", package)

    assert first["package_digest"] != second["package_digest"]
    assert sum(sql.startswith("INSERT INTO research_publications") for sql in db.statements) == 2


@pytest.mark.asyncio
async def test_publish_evidence_handles_insert_result_without_metadata(monkeypatch):
    package = {"run_id": "run-1", "claims": []}
    db = DB(non_dict_insert=True)
    env = SimpleNamespace(DB=db, EVIDENCE_PACKAGE_SIGNING_SECRET="secret")
    monkeypatch.setattr(worker, "verify_package", lambda *args, **kwargs: (True, None))
    monkeypatch.setattr(worker, "package_digest", lambda value: "digest-1")

    body, status = await worker._publish_evidence(env, "run-1", package)

    assert status == 200
    assert body["publication_id"] is None
    assert body["publication_state"] == "published"
