import pytest
from types import SimpleNamespace

from backend.worker_research import ingest_sources


@pytest.mark.asyncio
async def test_research_source_fetch_errors_are_redacted():
    async def failing_fetcher(url):
        raise RuntimeError("private endpoint and stack details")

    result = await ingest_sources(
        SimpleNamespace(),
        "run-1",
        SimpleNamespace(source_urls=("https://example.com",), max_sources=1),
        fetcher=failing_fetcher,
        persistence_cls=lambda env: object(),
    )

    assert result == [
        {
            "url": "https://example.com",
            "status": "error",
            "error": "source_fetch_failed",
        }
    ]
