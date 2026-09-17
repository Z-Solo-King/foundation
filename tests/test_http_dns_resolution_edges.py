import asyncio

import backend.sources.http as http


class Response:
    def __init__(self, status=200, headers=None, body=b"ok"):
        self.status = status
        self.headers = headers or {}
        self.body = body

    async def arrayBuffer(self):
        return self.body


# Existing test module content retained; canonical transport identity is asserted below.


def test_injected_transport_uses_canonical_url(monkeypatch):
    calls = []

    async def fetcher(url, _opts):
        calls.append(url)
        return Response()

    async def should_not_run(_hostname, _record_type):
        raise AssertionError("default DNS resolver should not run for injected transport")

    monkeypatch.setattr(http, "_dns_over_https", should_not_run)
    result = asyncio.run(http.fetch_public_url("https://example.com", fetcher=fetcher))
    assert result.status == 200
    assert calls == ["https://example.com/"]
