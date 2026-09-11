from datetime import datetime, timezone
from types import SimpleNamespace

import pytest

import backend.sources.http as source_http
import backend.sources.wikipedia as wikipedia
import worker
from backend.api.models import ResearchRequest
from backend.persistence.cloudflare import CloudflarePersistence, IdempotencyConflictError, request_fingerprint
from backend.persistence.d1 import D1Repository, DocumentVersionRecord, EvidenceRecord, RunRecord, SourceLineageRecord
from backend.persistence.r2 import ArtifactManifest, R2Artifact, R2Repository
from backend.sources.search import SearchAuthorization, SearchResult, search


class FakeStatement:
    def __init__(self, value=None): self.value, self.bound = value, ()
    def bind(self, *args): self.bound = args; return self
    async def run(self): return self.value or {"success": True}
    async def first(self): return self.value
    async def all(self): return self.value or []


class FakeDB:
    def __init__(self):
        self.statements = []
        self.batch_result = [SimpleNamespace(results=[]), SimpleNamespace(results=[]), SimpleNamespace(results=[])]
    def prepare(self, sql):
        statement = FakeStatement(); self.statements.append((sql, statement)); return statement
    async def batch(self, statements): return self.batch_result


class FakeArtifacts:
    def __init__(self): self.values = {}
    async def put(self, key, content, **kwargs): self.values[key] = content
    async def get(self, key):
        value = self.values.get(key)
        if value is None: return None
        return SimpleNamespace(body=SimpleNamespace(arrayBuffer=lambda: _return_bytes(value)))


async def _return_bytes(value): return value


def make_request(**changes):
    data = dict(question="test", depth="standard", require_citations=True, max_sources=2, max_evidence_items=4, strict_zero_cost_only=True, source_urls=())
    data.update(changes)
    return ResearchRequest(**data)


@pytest.mark.asyncio
async def test_search_contract_and_authorization():
    authorization = SearchAuthorization("test", True, True, True)
    async def implementation(query, limit): return [SearchResult("https://example.com", query, "snippet", "family")][:limit]
    results = await search("query", 1, authorization, implementation)
    assert results[0].title == "query"
    with pytest.raises(ValueError): await search("", 1, authorization, implementation)
    with pytest.raises(ValueError): await search("q", 0, authorization, implementation)
    with pytest.raises(PermissionError): await search("q", 1, SearchAuthorization("x", False, True, True), implementation)
    with pytest.raises(PermissionError): await search("q", 1, SearchAuthorization("x", True, False, True), implementation)
    with pytest.raises(PermissionError): await search("q", 1, SearchAuthorization("x", True, True, False), implementation)


class FakeHTTPResponse:
    def __init__(self, status=200, headers=None, body=b"ok", payload=None):
        self.status = status; self.headers = headers or {}; self._body = body; self._payload = payload or {}
    async def arrayBuffer(self): return self._body
    async def json(self): return self._payload


@pytest.mark.asyncio
async def test_public_http_validation_and_redirects():
    source_http.validate_url("https://example.com")
    for url in ("ftp://example.com", "http://127.0.0.1", "http://localhost", "https://user:pass@example.com", "https://example.com:8443"):
        with pytest.raises(ValueError): source_http.validate_url(url)
    responses = iter([FakeHTTPResponse(302, {"location": "/next"}), FakeHTTPResponse(200, {"content-type": "text/plain", "etag": "e1"}, b"hello")])
    async def fake_fetch(url, options): return next(responses)
    result = await source_http.fetch_public_url("https://example.com/start", fetcher=fake_fetch)
    assert result.final_url == "https://example.com/next" and result.content == b"hello"
    async def bad_redirect(url, options): return FakeHTTPResponse(302, {})
    with pytest.raises(RuntimeError, match="without Location"): await source_http.fetch_public_url("https://example.com/start", fetcher=bad_redirect)
    async def huge(url, options): return FakeHTTPResponse(200, body=b"x" * (source_http.MAX_BYTES + 1))
    with pytest.raises(RuntimeError, match="size budget"): await source_http.fetch_public_url("https://example.com/start", fetcher=huge)


@pytest.mark.asyncio
async def test_wikipedia_adapter_parses_results(monkeypatch):
    payload = {"query": {"search": [{"title":"A","pageid":1,"snippet":"s"},{"title":"","pageid":2},{"title":"B","pageid":None}]}}
    async def fake_fetch(url, options): return FakeHTTPResponse(200, payload=payload)
    monkeypatch.setattr(wikipedia, "_workers_fetch", lambda: fake_fetch)
    results = await wikipedia.wikipedia_search("query", 5)
    assert len(results) == 1 and results[0].title == "A"
    async def failed_fetch(url, options): return FakeHTTPResponse(503)
    monkeypatch.setattr(wikipedia, "_workers_fetch", lambda: failed_fetch)
    with pytest.raises(RuntimeError, match="HTTP 503"): await wikipedia.wikipedia_search("query", 1)


@pytest.mark.asyncio
async def test_cloudflare_persistence_helpers():
    request = make_request(source_urls=("https://example.com",))
    assert len(request_fingerprint(request)) == 64
    db = FakeDB(); artifacts = FakeArtifacts(); persistence = CloudflarePersistence(SimpleNamespace(DB=db, ARTIFACTS=artifacts))
    assert await persistence.create_run("run-1", request) == "run-1"
    with pytest.raises(ValueError): await persistence.create_run_idempotent(request, "")
    expected_hash = request_fingerprint(request)
    db.batch_result = [SimpleNamespace(results=[]), SimpleNamespace(results=[]), SimpleNamespace(results=[{"run_id":"run-abc","request_hash":expected_hash}])]
    assert await persistence.create_run_idempotent(request, "key-1") == "run-abc"
    db.batch_result[2].results[0]["request_hash"] = "different"
    with pytest.raises(IdempotencyConflictError): await persistence.create_run_idempotent(request, "key-1")
    db.batch_result[2].results = []
    with pytest.raises(RuntimeError, match="not persisted"): await persistence.create_run_idempotent(request, "key-2")
    await persistence.get_run("run-1")
    with pytest.raises(ValueError): await persistence.set_run_status("run-1", "bad")
    await persistence.set_run_status("run-1", "running")
    result = await persistence.put_artifact("k", b"abc", "text/plain")
    assert result["size"] == 3 and await persistence.get_artifact("k") == b"abc" and await persistence.get_artifact("missing") is None


def test_d1_repository_all_paths():
    repo = D1Repository(); now = datetime.now(timezone.utc)
    run = RunRecord("r1","q","standard","planned",now,now,1,2,"{}"); assert repo.create_run(run) is run
    with pytest.raises(ValueError): repo.create_run(run)
    assert repo.get_run("missing") is None
    assert repo.update_run(RunRecord("r1","q2","deep","running",now,now,2,3,"{}")).question == "q2"
    with pytest.raises(ValueError): repo.update_run(RunRecord("missing","q","standard","planned",now,now,1,1,"{}"))
    evidence = EvidenceRecord("e1","r1","o1","s1",None,0,3,"hash",now); assert repo.add_evidence(evidence) is evidence
    with pytest.raises(ValueError): repo.add_evidence(evidence)
    assert repo.evidence_for_run("r1") == [evidence] and repo.evidence_for_claim("missing") == []
    lineage = SourceLineageRecord("s1","f1",None,"origin",now,now); assert repo.upsert_lineage(lineage) is lineage
    assert repo.get_lineage("s1") is lineage and repo.get_lineage("missing") is None and repo.lineage_for_family("f1") == [lineage]
    version = DocumentVersionRecord("v1","o1","s1",now,None,"hash","artifact"); assert repo.add_version(version) is version
    with pytest.raises(ValueError): repo.add_version(version)
    assert repo.versions_for_observation("o1") == [version]


def test_r2_repository_all_paths():
    now = datetime.now(timezone.utc); repo = R2Repository(); artifact = R2Artifact("a1","project-artifacts","k","text/plain",3,now,"hash")
    assert repo.upload(artifact,b"abc") is artifact
    with pytest.raises(ValueError): repo.upload(artifact,b"abc")
    with pytest.raises(ValueError): repo.upload(R2Artifact("a2","project-artifacts","k2","text/plain",4,now,"hash"),b"abc")
    assert repo.download("a1")[1] == b"abc" and repo.download("missing") is None
    repo.delete("a1"); repo.delete("missing")
    manifest = ArtifactManifest("m1","name","desc","text",{"encoding":"utf-8"}); assert repo.add_manifest(manifest) is manifest
    with pytest.raises(ValueError): repo.add_manifest(manifest)
    assert repo.get_manifest("m1") is manifest and repo.get_manifest("missing") is None


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
