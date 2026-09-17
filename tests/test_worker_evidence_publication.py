from types import SimpleNamespace

import pytest

import worker
from backend.evidence_publication import package_digest, package_signature


class Statement:
    def __init__(self, value):
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
        return {"success": True}


class DB:
    def __init__(self, run=True, observations=None):
        self.run = {"run_id": "run-1"} if run else None
        self.observations = observations or [{"observation_id": "obs-1"}]
        self.writes = []

    def prepare(self, sql):
        if sql.startswith("SELECT run_id FROM research_runs"):
            return Statement(self.run)
        if sql.startswith("SELECT observation_id FROM observations"):
            return Statement(self.observations)
        statement = Statement(None)
        self.writes.append((sql, statement))
        return statement


def package():
    value = {
        "schema": "evidence-package/v1",
        "run_id": "run-1",
        "lineage": {"observation_ids": ["obs-1"]},
        "claims": [{"claim": "verified", "evidence_ids": ["obs-1"]}],
    }
    value["content_digest"] = package_digest(value)
    value["signature"] = package_signature(value, "secret")
    return value


@pytest.mark.asyncio
async def test_publish_evidence_rejects_missing_run_and_invalid_package():
    missing = SimpleNamespace(DB=DB(run=False), EVIDENCE_PACKAGE_SIGNING_SECRET="secret")
    body, status = await worker._publish_evidence(missing, "run-1", package())
    assert status == 404 and body["error"] == "run not found"

    env = SimpleNamespace(DB=DB(), EVIDENCE_PACKAGE_SIGNING_SECRET="secret")
    body, status = await worker._publish_evidence(env, "run-1", {"schema": "bad"})
    assert status == 400 and body["publication_state"] == "rejected"


@pytest.mark.asyncio
async def test_publish_evidence_persists_only_verified_package():
    db = DB()
    env = SimpleNamespace(DB=db, EVIDENCE_PACKAGE_SIGNING_SECRET="secret")
    body, status = await worker._publish_evidence(env, "run-1", package())
    assert status == 200
    assert body["publication_state"] == "published"
    assert body["package_digest"] == package()["content_digest"]
    assert db.writes
    assert "INSERT INTO research_publications" in db.writes[0][0]


class Request:
    def __init__(self, payload, authorization="Bearer secret"):
        self.method = "POST"
        self.url = "https://example.com/api/v1/research/publish"
        self._payload = payload
        self.headers = {"Authorization": authorization}

    async def json(self):
        return self._payload


@pytest.mark.asyncio
async def test_publish_endpoint_requires_auth_and_run_id():
    entry = worker.Default()
    entry.env = SimpleNamespace(
        DB=DB(),
        EVIDENCE_PACKAGE_SIGNING_SECRET="secret",
        ENVIRONMENT="production",
        AUTH_TOKEN="secret",
    )
    unauthorized = await entry.fetch(Request({"run_id": "run-1", "package": package()}, "Bearer wrong"))
    assert "unauthorized" in str(unauthorized)

    missing_run = await entry.fetch(Request({"package": package()}))
    assert "run_id is required" in str(missing_run)

    published = await entry.fetch(Request({"run_id": "run-1", "package": package()}))
    assert published
