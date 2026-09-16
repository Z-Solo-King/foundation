from types import SimpleNamespace

import pytest

from backend.worker_research import ingest_sources


class _Stmt:
    def bind(self, *args):
        return self

    async def run(self):
        return None


class _DB:
    def prepare(self, _sql):
        return _Stmt()


class _Persistence:
    def __init__(self, env):
        self.env = env

    async def put_artifact(self, *_args, **_kwargs):
        return None


class _Fetched:
    def __init__(self, url):
        self.final_url = url
        self.content = b"ok"
        self.content_type = "text/plain"
        self.etag = None
        self.status = 200


@pytest.mark.asyncio
async def test_ingest_sources_keeps_successful_sources_when_one_fetch_fails():
    calls = []

    async def fetcher(url):
        calls.append(url)
        if url.endswith("/bad"):
            raise ValueError("blocked host")
        return _Fetched(url)

    env = SimpleNamespace(DB=_DB())
    req = SimpleNamespace(source_urls=("https://example.test/good", "https://example.test/bad"), max_sources=2)
    results = await ingest_sources(env, "run-1", req, fetcher=fetcher, persistence_cls=_Persistence)

    assert calls == ["https://example.test/good", "https://example.test/bad"]
    assert results[0]["status"] == 200
    assert results[1] == {"url": "https://example.test/bad", "status": "error", "error": "blocked host"}
