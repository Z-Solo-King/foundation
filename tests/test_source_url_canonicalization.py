import pytest

import backend.sources.http as source_http


class Response:
    def __init__(self, status=200, headers=None, body=b"ok"):
        self.status = status
        self.headers = headers or {}
        self.body = body

    async def arrayBuffer(self):
        return self.body


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        ("HTTPS://EXAMPLE.COM.:443/path#fragment", "https://example.com/path"),
        ("http://EXAMPLE.COM:80", "http://example.com/"),
        ("https://example.com", "https://example.com/"),
        ("https://example.com:80/path", "https://example.com:80/path"),
    ],
)
def test_canonicalize_url_normalizes_security_neutral_variants(source, expected):
    assert source_http.canonicalize_url(source) == expected


@pytest.mark.parametrize(
    "source",
    [
        "ftp://example.com",
        "https://user:pass@example.com",
        "https://127.0.0.1",
        "https://example.com:8443",
    ],
)
def test_canonicalize_url_rejects_unsafe_or_unsupported_forms(source):
    with pytest.raises(ValueError):
        source_http.canonicalize_url(source)


@pytest.mark.asyncio
async def test_fetch_public_url_uses_canonical_fetch_identity():
    calls = []

    async def fetcher(url, options):
        calls.append(url)
        return Response()

    result = await source_http.fetch_public_url("HTTPS://EXAMPLE.COM.:443/path#fragment", fetcher=fetcher)
    assert calls == ["https://example.com/path"]
    assert result.url == "https://example.com/path"
    assert result.final_url == "https://example.com/path"


@pytest.mark.asyncio
async def test_fetch_public_url_rejects_https_to_http_redirect_downgrade():
    async def fetcher(url, options):
        return Response(302, {"location": "http://example.com/plain"})

    with pytest.raises(ValueError, match="downgrade"):
        await source_http.fetch_public_url("https://example.com/start", fetcher=fetcher)


@pytest.mark.asyncio
async def test_fetch_public_url_revalidates_each_redirect_destination():
    responses = iter(
        [
            Response(302, {"location": "https://example.com/next"}),
            Response(200, body=b"ok"),
        ]
    )
    calls = []

    async def fetcher(url, options):
        calls.append(url)
        return next(responses)

    result = await source_http.fetch_public_url("https://example.com/start", fetcher=fetcher)
    assert calls == ["https://example.com/start", "https://example.com/next"]
    assert result.final_url == "https://example.com/next"
