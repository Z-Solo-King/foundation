import asyncio
from types import SimpleNamespace


def test_worker_http_entrypoint_all_paths():
    import worker
    class Req:
        def __init__(self, method, url, payload=None, headers=None): self.method, self.url, self._payload, self.headers = method, url, payload, headers or {}
        async def json(self): return self._payload
    class DBStatement:
        def __init__(self, first=None, all_rows=None): self.first_value, self.all_rows = first, all_rows or []
        def bind(self,*args): return self
        async def run(self): return {"success":True}
        async def first(self): return self.first_value
        async def all(self): return self.all_rows
    class DB:
        def prepare(self, sql): return DBStatement()
    class Art:
        async def put(self,*args,**kwargs): pass
    env=SimpleNamespace(DB=DB(),ARTIFACTS=Art(),ENVIRONMENT="development",AUTH_TOKEN=None,CONTROL_PLANE=None)
    entry=worker.Default(); entry.env=env
    assert asyncio.run(entry.fetch(Req("GET","https://x/health")))
    assert asyncio.run(entry.fetch(Req("GET","https://x/readiness")))
    assert asyncio.run(entry.fetch(Req("GET","https://x/nope")))
    assert asyncio.run(entry.fetch(Req("GET","https://x/api/v1/research/r")))
    assert asyncio.run(entry.fetch(Req("POST","https://x/api/v1/research",[])))
    assert asyncio.run(entry.fetch(Req("POST","https://x/api/v1/research",{"question":"q"})))


def test_authenticated_public_research_read_supports_pagination_and_boundaries():
    import asyncio
    import worker

    class Req:
        def __init__(self, method, url, payload=None, headers=None):
            self.method, self.url, self._payload, self.headers = method, url, payload, headers or {}
        async def json(self):
            return self._payload

    subject = __import__("hashlib").sha256(b"token").hexdigest()

    class DBStatement:
        def __init__(self, sql):
            self.sql = sql
        def bind(self, *args):
            self.args = args
            return self
        async def first(self):
            if "FROM research_runs" in self.sql:
                return {
                    "run_id": "run-1",
                    "status": "completed",
                    "created_at": "2026-09-18T03:00:00+00:00",
                    "updated_at": "2026-09-18T03:10:00+00:00",
                    "depth": "standard",
                    "require_citations": 1,
                    "max_sources": 20,
                    "max_evidence_items": 100,
                }
            return None
        async def all(self):
            if "FROM observations" in self.sql:
                return [
                    {"observation_id": "o1", "source_id": "s1", "version_id": "v1", "observed_at": "2026-09-18T03:01:00+00:00", "retrieval_method": "http_fetch", "content_hash": "h1", "integrity_state": "verified", "access_state": "accessible", "url": "https://example.test/1", "source_family_id": "example.test"},
                    {"observation_id": "o2", "source_id": "s2", "version_id": "v2", "observed_at": "2026-09-18T03:02:00+00:00", "retrieval_method": "http_fetch", "content_hash": "h2", "integrity_state": "verified", "access_state": "accessible", "url": "https://example.test/2", "source_family_id": "example.test"},
                ]
            return []

    class DB:
        def prepare(self, sql):
            return DBStatement(sql)

    class Art:
        async def put(self, *args, **kwargs):
            pass

    env = SimpleNamespace(
        DB=DB(),
        ARTIFACTS=Art(),
        ENVIRONMENT="production",
        AUTH_TOKEN="token",
        CONTROL_PLANE=None,
    )
    entry = worker.Default()
    entry.env = env

    response = asyncio.run(entry.fetch(Req(
        "GET",
        "https://x/api/v1/research/run-1?limit=1",
        headers={"Authorization": "Bearer token"},
    )))
    assert response.status == 200

    bad_limit = asyncio.run(entry.fetch(Req(
        "GET",
        "https://x/api/v1/research/run-1?limit=nope",
        headers={"Authorization": "Bearer token"},
    )))
    assert bad_limit.status == 400

    oversized = asyncio.run(entry.fetch(Req(
        "GET",
        "https://x/api/v1/research/run-1?limit=51",
        headers={"Authorization": "Bearer token"},
    )))
    assert oversized.status == 400

    bad_cursor = asyncio.run(entry.fetch(Req(
        "GET",
        "https://x/api/v1/research/run-1?limit=1&cursor=bad",
        headers={"Authorization": "Bearer token"},
    )))
    assert bad_cursor.status == 400
