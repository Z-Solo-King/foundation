from __future__ import annotations

from dataclasses import dataclass
from types import SimpleNamespace

import pytest

from backend.worker_research import ingest_sources


@dataclass
class FakeStatement:
    sql: str
    bindings: tuple[object, ...]

    def bind(self, *values: object) -> "FakeStatement":
        self.bindings = values
        return self


class FakeDB:
    def __init__(self) -> None:
        self.prepared: list[FakeStatement] = []
        self.batched: list[list[FakeStatement]] = []

    def prepare(self, sql: str) -> FakeStatement:
        statement = FakeStatement(sql, ())
        self.prepared.append(statement)
        return statement

    async def batch(self, statements: list[FakeStatement]) -> None:
        self.batched.append(statements)


class FakePersistence:
    def __init__(self, env) -> None:
        self.env = env
        self.artifacts: list[tuple[str, bytes, str]] = []

    async def put_artifact(self, ref: str, content: bytes, *, content_type: str) -> None:
        self.artifacts.append((ref, content, content_type))


class FakeFetcher:
    def __init__(self) -> None:
        self.urls: list[str] = []

    async def __call__(self, url: str):
        self.urls.append(url)
        return SimpleNamespace(
            final_url=url,
            content=f"body:{url}".encode(),
            content_type="text/plain",
            status=200,
            etag="etag",
        )


class Request:
    source_urls = ["https://one.example", "https://two.example"]
    max_sources = 2


@pytest.mark.asyncio
async def test_ingest_sources_batches_d1_writes_once_for_all_successful_sources() -> None:
    db = FakeDB()
    env = SimpleNamespace(DB=db)
    fetcher = FakeFetcher()

    results = await ingest_sources(env, "run-1", Request(), fetcher=fetcher, persistence_cls=FakePersistence)

    assert len(results) == 2
    assert fetcher.urls == Request.source_urls
    assert len(db.batched) == 1
    assert len(db.batched[0]) == 6
    assert len(db.prepared) == 6
    assert all(statement.bindings for statement in db.batched[0])


@pytest.mark.asyncio
async def test_ingest_sources_with_no_sources_skips_empty_batch() -> None:
    db = FakeDB()
    env = SimpleNamespace(DB=db)
    request = SimpleNamespace(source_urls=(), max_sources=2)

    results = await ingest_sources(env, "run-empty", request, fetcher=FakeFetcher(), persistence_cls=FakePersistence)

    assert results == []
    assert db.prepared == []
    assert db.batched == []


@pytest.mark.asyncio
async def test_ingest_sources_rejects_oversized_response_before_persistence() -> None:
    db = FakeDB()
    env = SimpleNamespace(DB=db)

    class LargeFetcher:
        async def __call__(self, url: str):
            return SimpleNamespace(
                final_url=url,
                content=b"x" * (10 * 1024 * 1024 + 1),
                content_type="application/octet-stream",
                status=200,
                etag=None,
            )

    results = await ingest_sources(
        env,
        "run-large",
        SimpleNamespace(source_urls=["https://large.example"], max_sources=1),
        fetcher=LargeFetcher(),
        persistence_cls=FakePersistence,
    )
    assert results == [{
        "url": "https://large.example",
        "status": "too_large",
        "error": "source response exceeds supported size",
        "bytes": 10 * 1024 * 1024 + 1,
        "max_bytes": 10 * 1024 * 1024,
    }]
    assert db.prepared == []
    assert db.batched == []
