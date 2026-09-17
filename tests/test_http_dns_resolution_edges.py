import asyncio
from types import SimpleNamespace

import pytest


class _DnsResponse:
    def __init__(self, status, payload):
        self.status = status
        self.payload = payload

    async def json(self):
        return self.payload


@pytest.mark.parametrize("status", [400, 500])
def test_dns_over_https_non_200_fails_closed(monkeypatch, status):
    import backend.sources.http as http

    async def fetcher(_url, _opts):
        return _DnsResponse(status, {})

    monkeypatch.setattr(http, "_workers_fetch", lambda: fetcher)
    with pytest.raises(RuntimeError, match="DNS resolution failed"):
        asyncio.run(http._dns_over_https("example.com", "A"))


def test_dns_over_https_rejects_non_mapping_payload(monkeypatch):
    import backend.sources.http as http

    async def fetcher(_url, _opts):
        return _DnsResponse(200, [])

    monkeypatch.setattr(http, "_workers_fetch", lambda: fetcher)
    with pytest.raises(RuntimeError, match="invalid DNS response"):
        asyncio.run(http._dns_over_https("example.com", "AAAA"))


def test_dns_over_https_filters_non_address_records_and_blank_data(monkeypatch):
    import backend.sources.http as http

    payload = {
        "Answer": [
            {"type": 5, "data": "alias.example.com"},
            {"type": 1, "data": ""},
            {"type": 28, "data": "2001:db8::1"},
            "not-a-record",
        ]
    }

    async def fetcher(_url, _opts):
        return _DnsResponse(200, payload)

    monkeypatch.setattr(http, "_workers_fetch", lambda: fetcher)
    assert asyncio.run(http._dns_over_https("example.com", "A")) == ["2001:db8::1"]


def test_public_destination_fails_when_dns_returns_no_addresses():
    import backend.sources.http as http

    async def resolver(_hostname, _record_type):
        return []

    with pytest.raises(ValueError, match="did not resolve"):
        asyncio.run(http._validate_public_destination("https://example.com", resolver=resolver))


def test_public_destination_rejects_invalid_resolved_address():
    import backend.sources.http as http

    async def resolver(_hostname, _record_type):
        return ["not-an-ip"]

    with pytest.raises(ValueError, match="invalid address"):
        asyncio.run(http._validate_public_destination("https://example.com", resolver=resolver))


def test_public_destination_propagates_resolver_failure():
    import backend.sources.http as http

    async def resolver(_hostname, _record_type):
        raise RuntimeError("resolver unavailable")

    with pytest.raises(RuntimeError, match="resolver unavailable"):
        asyncio.run(http._validate_public_destination("https://example.com", resolver=resolver))


def test_custom_transport_without_resolver_uses_only_url_validation(monkeypatch):
    import backend.sources.http as http

    calls = []

    class Response:
        status = 200
        headers = {}

        async def arrayBuffer(self):
            return b"ok"

    async def fetcher(url, _opts):
        calls.append(url)
        return Response()

    async def should_not_run(_hostname, _record_type):
        raise AssertionError("default DNS resolver should not run for injected transport")

    monkeypatch.setattr(http, "_dns_over_https", should_not_run)
    result = asyncio.run(http.fetch_public_url("https://example.com", fetcher=fetcher))
    assert result.status == 200
    assert calls == ["https://example.com/"]
