import asyncio
from types import SimpleNamespace

import pytest

from backend.persistence.d1 import D1Repository
from backend.persistence.r2 import R2Repository
from backend.sources import http as source_http
import worker


class FakeStatement:
    def __init__(self, rows=(), first=None):
        self.rows = list(rows)
        self.first_value = first
        self.args = None

    def bind(self, *args):
        self.args = args
        return self

    async def all(self):
        return {"results": self.rows}

    async def first(self):
        return self.first_value

    async def run(self):
        return {"success": True}


class FakeDB:
    def __init__(self):
        self.calls = []

    def prepare(self, sql):
        self.calls.append(sql)
        return FakeStatement()


class FakeArtifacts:
    def __init__(self):
        self.values = {}

    async def put(self, key, value, **kwargs):
        self.values[key] = value


class FakeRepo:
    def __init__(self):
        self.rows = {"x": {"id": "x"}}

    async def get(self, key):
        return self.rows.get(key)

    async def put(self, key, value):
        self.rows[key] = value


def make_request(source_urls=()):
    from backend.api.models import ResearchRequest
    return ResearchRequest(question="q", source_urls=source_urls)


def test_search_contract_and_authorization():
    from backend.sources.search import SearchRequest, authorize_search
    assert SearchRequest(query="q", limit=2).limit == 2
    assert authorize_search("token", "token") is True
    assert authorize_search("bad", "token") is False


@pytest.mark.asyncio
async def test_public_http_validation_and_redirects(monkeypatch):
    from backend.sources.http import FetchResult, fetch_public_url
    async def fake(url):
        return FetchResult(url, url, 200, "text/plain", b"ok", None)
    assert await fetch_public_url("https://example.com", fetcher=fake)
    with pytest.raises(ValueError):
        await fetch_public_url("http://127.0.0.1")


@pytest.mark.asyncio
async def test_wikipedia_adapter_parses_results(monkeypatch):
    from backend.sources.wikipedia import _implementation
    async def fake(url):
        return source_http.FetchResult(url, url, 200, "application/json", b'{"query":{"search":[{"title":"A"}]}}', None)
    results = await _implementation("test", 2, fetcher=fake)
    assert results[0]["title"] == "A"


def test_cloudflare_persistence_helpers():
    repo = D1Repository(FakeDB())
    assert repo.db is not None
    r2 = R2Repository(FakeRepo())
    manifest = {"id": "m1"}
    asyncio.run(r2.put_manifest("m1", manifest))
    assert asyncio.run(r2.get_manifest("m1")) == manifest
    assert asyncio.run(r2.get_manifest("missing")) is None


@pytest.mark.asyncio
async def test_worker_helpers_and_source_ingestion(monkeypatch):
    request = make_request(source_urls=("https://example.com",))
    assert worker._bearer_token(SimpleNamespace(headers={"Authorization":"Bearer abc"})) == "abc"
    assert worker._bearer_token(SimpleNamespace(headers={"Authorization":"Basic abc"})) is None
    assert worker._authorized(SimpleNamespace(headers={}), SimpleNamespace(ENVIRONMENT="development", AUTH_TOKEN=None)) is True
    assert worker._authorized(SimpleNamespace(headers={"Authorization":"Bearer bad"}), SimpleNamespace(ENVIRONMENT="production", AUTH_TOKEN="good")) is False
    class Request:
        async def json(self): return {"ok":True}
    assert await worker._json(Request()) == {"ok":True}
    class BadRequest:
        async def json(self): raise RuntimeError("bad json")
    assert await worker._json(BadRequest()) is None
    db = FakeDB(); artifacts = FakeArtifacts(); env = SimpleNamespace(DB=db, ARTIFACTS=artifacts, ENVIRONMENT="development", AUTH_TOKEN=None)
    async def fake_public(url): return source_http.FetchResult(url,url,200,"text/plain",b"abc","e")
    monkeypatch.setattr(worker,"fetch_public_url",fake_public)
    ingested = await worker._ingest_sources(env,"run-1",request); assert ingested[0]["bytes"] == 3
    assert await worker._control_plane_ready(SimpleNamespace(CONTROL_PLANE=None)) is False
    class Control:
        async def fetch(self,url): return SimpleNamespace(status=200)
    assert await worker._control_plane_ready(SimpleNamespace(CONTROL_PLANE=Control())) is True
    class FailingControl:
        async def fetch(self,url): raise RuntimeError("down")
    assert await worker._control_plane_ready(SimpleNamespace(CONTROL_PLANE=FailingControl())) is False
