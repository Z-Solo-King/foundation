"""Wikimedia search adapter.

Wikimedia exposes a MediaWiki search API at each wiki's /w/api.php endpoint.
This adapter is deliberately isolated so provider policy can enable/disable it.
"""

from urllib.parse import urlencode
from workers import fetch

from .search import SearchResult, SearchAuthorization, search

WIKIPEDIA_AUTHORIZATION = SearchAuthorization(
    provider="wikimedia",
    free_eligible=True,
    pricing_verified=True,
    no_overage=True,
)


async def _implementation(query: str, limit: int) -> list[SearchResult]:
    params = urlencode({
        "action": "query",
        "list": "search",
        "srsearch": query,
        "srlimit": min(limit, 20),
        "format": "json",
        "formatversion": 2,
        "origin": "*",
    })
    url = f"https://en.wikipedia.org/w/api.php?{params}"
    response = await fetch(url, {"headers": {"User-Agent": "ResearchIntelligenceEngine/0.1"}})
    if int(response.status) != 200:
        raise RuntimeError(f"Wikimedia search failed with HTTP {response.status}")
    payload = await response.json()
    results = []
    for item in payload.get("query", {}).get("search", []):
        title = item.get("title", "")
        pageid = item.get("pageid")
        if not title or not pageid:
            continue
        results.append(SearchResult(
            url=f"https://en.wikipedia.org/?curid={pageid}",
            title=title,
            snippet=item.get("snippet", ""),
            source_family="en.wikipedia.org",
        ))
    return results


async def wikipedia_search(query: str, limit: int = 5) -> list[SearchResult]:
    return await search(query, limit, WIKIPEDIA_AUTHORIZATION, _implementation)
