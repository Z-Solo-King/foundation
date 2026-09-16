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
