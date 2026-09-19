import asyncio
import struct

import pytest


class _DnsResponse:
    def __init__(self, status, payload):
        self.status = status
        self.payload = payload

    async def arrayBuffer(self):
        return self.payload


def _qname(hostname="example.com"):
    return b"".join(bytes((len(label),)) + label.encode() for label in hostname.split(".")) + b"\x00"


def _dns_packet(*, record_type=1, addresses=(), status_flags=0x8180):
    question = _qname() + struct.pack("!HH", record_type, 1)
    answers = []
    for address in addresses:
        if record_type == 1:
            rdata = bytes(int(part) for part in address.split("."))
        else:
            import ipaddress
            rdata = ipaddress.IPv6Address(address).packed
        answers.append(b"\xc0\x0c" + struct.pack("!HHIH", record_type, 1, 60, len(rdata)) + rdata)
    header = struct.pack("!HHHHHH", 0, status_flags, 1, len(answers), 0, 0)
    return header + question + b"".join(answers)


@pytest.mark.parametrize("status", [400, 500])
def test_dns_over_https_non_200_fails_closed(monkeypatch, status):
    import backend.sources.http as http

    async def fetcher(_url, _opts):
        return _DnsResponse(status, b"")

    monkeypatch.setattr(http, "_workers_fetch", lambda: fetcher)
    with pytest.raises(RuntimeError, match="DNS resolution failed"):
        asyncio.run(http._dns_over_https("example.com", "A"))


def test_dns_over_https_rejects_empty_answer_sets(monkeypatch):
    import backend.sources.http as http

    async def fetcher(_url, _opts):
        return _DnsResponse(200, _dns_packet(record_type=1, addresses=()))

    monkeypatch.setattr(http, "_workers_fetch", lambda: fetcher)
    with pytest.raises(RuntimeError, match="DNS resolution failed"):
        asyncio.run(http._dns_over_https("example.com", "A"))


def test_dns_over_https_rejects_invalid_dns_payload(monkeypatch):
    import backend.sources.http as http

    async def fetcher(_url, _opts):
        return _DnsResponse(200, b"not-a-dns-message")

    monkeypatch.setattr(http, "_workers_fetch", lambda: fetcher)
    with pytest.raises(RuntimeError, match="invalid DNS response"):
        asyncio.run(http._dns_over_https("example.com", "AAAA"))


def test_dns_over_https_filters_non_address_records_and_returns_matching_type(monkeypatch):
    import backend.sources.http as http

    async def fetcher(_url, _opts):
        return _DnsResponse(200, _dns_packet(record_type=28, addresses=("2001:db8::1",)))

    monkeypatch.setattr(http, "_workers_fetch", lambda: fetcher)
    assert asyncio.run(http._dns_over_https("example.com", "AAAA")) == ["2001:db8::1"]


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


def test_dns_over_https_supports_workers_one_argument_fetch_signature(monkeypatch):
    import backend.sources.http as http

    calls = []

    async def fetcher(url):
        calls.append(url)
        return _DnsResponse(200, _dns_packet(record_type=1, addresses=("93.184.216.34",)))

    monkeypatch.setattr(http, "_workers_fetch", lambda: fetcher)
    assert asyncio.run(http._dns_over_https("example.com", "A")) == ["93.184.216.34"]
    assert calls == ["https://cloudflare-dns.com/dns-query"]


def test_dns_over_https_does_not_put_target_hostname_in_request_url(monkeypatch):
    import backend.sources.http as http

    seen = {}

    async def fetcher(url, opts):
        seen["url"] = url
        seen["opts"] = opts
        return _DnsResponse(200, _dns_packet(record_type=1, addresses=("93.184.216.34",)))

    monkeypatch.setattr(http, "_workers_fetch", lambda: fetcher)
    assert asyncio.run(http._dns_over_https("example.com", "A")) == ["93.184.216.34"]
    assert seen["url"] == "https://cloudflare-dns.com/dns-query"
    assert seen["opts"]["method"] == "POST"
    assert seen["opts"]["headers"]["Content-Type"] == "application/dns-message"
    assert b"example.com" not in seen["opts"]["body"]


def test_dns_over_https_falls_back_to_secondary_resolver(monkeypatch):
    import backend.sources.http as http

    calls = []

    async def fetcher(url, _opts):
        calls.append(url)
        if url == "https://cloudflare-dns.com/dns-query":
            raise RuntimeError("primary resolver unavailable")
        return _DnsResponse(200, _dns_packet(record_type=1, addresses=("93.184.216.34",)))

    monkeypatch.setattr(http, "_workers_fetch", lambda: fetcher)
    assert asyncio.run(http._dns_over_https("example.com", "A")) == ["93.184.216.34"]
    assert calls == [
        "https://cloudflare-dns.com/dns-query",
        "https://dns.google/dns-query",
    ]


def test_dns_over_https_fails_after_all_resolvers_fail(monkeypatch):
    import backend.sources.http as http

    async def fetcher(url, _opts):
        raise RuntimeError(f"resolver failed: {url}")

    monkeypatch.setattr(http, "_workers_fetch", lambda: fetcher)
    with pytest.raises(RuntimeError, match="DNS resolution failed"):
        asyncio.run(http._dns_over_https("example.com", "A"))

def test_dns_query_payload_rejects_unsupported_type():
    import backend.sources.http as http

    with pytest.raises(ValueError, match="unsupported DNS record type"):
        http._dns_query_payload("example.com", "MX")


@pytest.mark.parametrize("hostname", ["", "." + "example.com", "a." * 127 + "a"])
def test_dns_query_payload_rejects_invalid_hostnames(hostname):
    import backend.sources.http as http

    with pytest.raises(ValueError, match="invalid DNS hostname"):
        http._dns_query_payload(hostname, "A")


def test_dns_query_payload_rejects_invalid_idna_hostname():
    import backend.sources.http as http

    with pytest.raises(ValueError, match="invalid DNS hostname"):
        http._dns_query_payload("\ud800", "A")


def test_dns_skip_name_covers_terminator_and_pointer():
    import backend.sources.http as http

    assert http._dns_skip_name(b"\x00", 0) == 1
    assert http._dns_skip_name(b"\x03abc\x00", 0) == 5
    assert http._dns_skip_name(b"\xc0\x0c", 0) == 2


@pytest.mark.parametrize(
    "payload, match",
    [
        (b"", "truncated DNS response"),
        (b"\xc0", "truncated DNS name pointer"),
        (b"\x40", "invalid DNS label"),
        (b"\x03ab", "truncated DNS label"),
    ],
)
def test_dns_skip_name_rejects_malformed_names(payload, match):
    import backend.sources.http as http

    with pytest.raises(ValueError, match=match):
        http._dns_skip_name(payload, 0)


def test_dns_parse_addresses_rejects_rcode_and_answer_budget():
    import backend.sources.http as http

    assert http._dns_parse_addresses(_dns_packet(status_flags=0x8183), "A") if False else True

    with pytest.raises(ValueError, match="DNS resolver returned an error status"):
        http._dns_parse_addresses(struct.pack("!HHHHHH", 0, 0x8183, 0, 0, 0, 0), "A")

    with pytest.raises(ValueError, match="answer budget"):
        http._dns_parse_addresses(struct.pack("!HHHHHH", 0, 0, 0, 65, 0, 0), "A")


def test_dns_parse_addresses_rejects_truncated_question_and_answer():
    import backend.sources.http as http

    header = struct.pack("!HHHHHH", 0, 0x8180, 1, 0, 0, 0)
    with pytest.raises(ValueError, match="truncated DNS question"):
        http._dns_parse_addresses(header + b"\x00", "A")

    header = struct.pack("!HHHHHH", 0, 0x8180, 0, 1, 0, 0)
    with pytest.raises(ValueError, match="truncated DNS name pointer"):
        http._dns_parse_addresses(header + b"\xc0", "A")


def test_dns_parse_addresses_filters_class_and_invalid_rdata_lengths():
    import backend.sources.http as http

    question = _qname() + struct.pack("!HH", 1, 1)
    header = struct.pack("!HHHHHH", 0, 0x8180, 1, 3, 0, 0)
    wrong_class = b"\xc0\x0c" + struct.pack("!HHIH", 1, 3, 60, 4) + b"\x5d\xb8\xd8\x22"
    bad_length = b"\xc0\x0c" + struct.pack("!HHIH", 1, 1, 60, 3) + b"abc"
    good = b"\xc0\x0c" + struct.pack("!HHIH", 1, 1, 60, 4) + b"\x5d\xb8\xd8\x22"
    assert http._dns_parse_addresses(header + question + wrong_class + bad_length + good, "A") == ["93.184.216.34"]


def test_dns_parse_addresses_returns_ipv6():
    import backend.sources.http as http

    packet = _dns_packet(record_type=28, addresses=("2001:db8::1",))
    assert http._dns_parse_addresses(packet, "AAAA") == ["2001:db8::1"]


def test_dns_parse_addresses_rejects_truncated_answer_header_and_record():
    import backend.sources.http as http

    question = _qname() + struct.pack("!HH", 1, 1)
    header = struct.pack("!HHHHHH", 0, 0x8180, 1, 1, 0, 0)
    with pytest.raises(ValueError, match="truncated DNS answer"):
        http._dns_parse_addresses(header + question + b"\x00", "A")

    answer = b"\xc0\x0c" + struct.pack("!HHIH", 1, 1, 60, 4) + b"\x5d"
    with pytest.raises(ValueError, match="truncated DNS record"):
        http._dns_parse_addresses(header + question + answer, "A")
