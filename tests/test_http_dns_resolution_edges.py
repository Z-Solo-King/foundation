import asyncio
import base64
import struct

import pytest


class _DnsResponse:
    def __init__(self, status, payload):
        self.status = status
        self.payload = payload
        self.headers = {"content-type": "application/dns-message"}

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


def _patch_doh(monkeypatch, response_factory):
    import backend.sources.http as http

    calls = []

    async def doh_request(endpoint, encoded_query):
        calls.append((endpoint, encoded_query))
        return await response_factory(endpoint, encoded_query)

    monkeypatch.setattr(http, "_doh_request", doh_request)
    return http, calls


@pytest.mark.parametrize("status", [400, 500])
def test_dns_over_https_non_200_fails_closed(monkeypatch, status):
    async def response_factory(_endpoint, _encoded_query):
        return _DnsResponse(status, b"")

    http, _ = _patch_doh(monkeypatch, response_factory)
    with pytest.raises(RuntimeError, match="DNS resolution failed"):
        asyncio.run(http._dns_over_https("example.com", "A"))


def test_dns_over_https_rejects_empty_answer_sets(monkeypatch):
    async def response_factory(_endpoint, _encoded_query):
        return _DnsResponse(200, _dns_packet(record_type=1, addresses=()))

    http, _ = _patch_doh(monkeypatch, response_factory)
    with pytest.raises(RuntimeError, match="DNS resolution failed"):
        asyncio.run(http._dns_over_https("example.com", "A"))


def test_dns_over_https_rejects_invalid_dns_payload(monkeypatch):
    async def response_factory(_endpoint, _encoded_query):
        return _DnsResponse(200, b"not-a-dns-message")

    http, _ = _patch_doh(monkeypatch, response_factory)
    with pytest.raises(RuntimeError, match="invalid DNS response"):
        asyncio.run(http._dns_over_https("example.com", "AAAA"))


def test_dns_over_https_filters_non_address_records_and_returns_matching_type(monkeypatch):
    async def response_factory(_endpoint, _encoded_query):
        return _DnsResponse(200, _dns_packet(record_type=28, addresses=("2001:db8::1",)))

    http, _ = _patch_doh(monkeypatch, response_factory)
    assert asyncio.run(http._dns_over_https("example.com", "AAAA")) == ["2001:db8::1"]


def test_dns_over_https_encodes_wire_query_without_plain_hostname_in_transport(monkeypatch):
    seen = []

    async def response_factory(endpoint, encoded_query):
        import base64

        decoded = base64.urlsafe_b64decode(encoded_query + "=" * (-len(encoded_query) % 4))
        seen.append((endpoint, encoded_query, decoded))
        return _DnsResponse(200, _dns_packet(record_type=1, addresses=("93.184.216.34",)))

    http, _calls = _patch_doh(monkeypatch, response_factory)
    assert asyncio.run(http._dns_over_https("example.com", "A")) == ["93.184.216.34"]
    assert seen
    endpoint, encoded_query, decoded = seen[0]
    assert endpoint == "https://cloudflare-dns.com/dns-query"
    assert "example.com" not in encoded_query
    assert b"example" in decoded and b"com" in decoded


def test_dns_over_https_falls_back_to_secondary_resolver(monkeypatch):
    async def response_factory(endpoint, _encoded_query):
        if endpoint == "https://cloudflare-dns.com/dns-query":
            raise RuntimeError("primary resolver unavailable")
        return _DnsResponse(200, _dns_packet(record_type=1, addresses=("93.184.216.34",)))

    http, calls = _patch_doh(monkeypatch, response_factory)
    assert asyncio.run(http._dns_over_https("example.com", "A")) == ["93.184.216.34"]
    assert [endpoint for endpoint, _ in calls] == [
        "https://cloudflare-dns.com/dns-query",
        "https://dns.google/dns-query",
    ]


def test_dns_over_https_fails_after_all_resolvers_fail(monkeypatch):
    async def response_factory(endpoint, _encoded_query):
        raise RuntimeError(f"resolver failed: {endpoint}")

    http, _ = _patch_doh(monkeypatch, response_factory)
    with pytest.raises(RuntimeError, match="DNS resolution failed"):
        asyncio.run(http._dns_over_https("example.com", "A"))


def test_doh_request_rejects_non_allowlisted_endpoint():
    import backend.sources.http as http

    with pytest.raises(ValueError, match="unsupported DNS-over-HTTPS endpoint"):
        asyncio.run(http._doh_request("https://attacker.example/dns-query", "AQID"))


def test_doh_request_constructs_fixed_url_and_get_options(monkeypatch):
    import backend.sources.http as http

    captured = {}

    class FakeObject:
        @staticmethod
        def fromEntries(value):
            return value

    async def fake_fetch(url, options):
        captured["url"] = url
        captured["options"] = options
        return "response"

    monkeypatch.setitem(__import__("sys").modules, "js", __import__("types").SimpleNamespace(
        Object=FakeObject,
        fetch=fake_fetch,
    ))
    monkeypatch.setitem(__import__("sys").modules, "pyodide.ffi", __import__("types").SimpleNamespace(
        to_js=lambda value, dict_converter=None: dict_converter(value) if dict_converter else value,
    ))

    result = asyncio.run(http._doh_request(
        "https://cloudflare-dns.com/dns-query",
        "AQID",
    ))
    assert result == "response"
    assert captured["url"] == "https://cloudflare-dns.com/dns-query?dns=AQID"
    assert captured["options"]["method"] == "GET"
    assert captured["options"]["headers"]["Accept"] == "application/dns-message"


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

def test_dns_query_payload_rejects_empty_label():
    import backend.sources.http as http

    with pytest.raises(ValueError, match="invalid DNS hostname"):
        http._dns_query_payload("example..com", "A")


def test_dns_parse_addresses_rejects_short_packet():
    import backend.sources.http as http

    with pytest.raises(ValueError, match="truncated DNS response"):
        http._dns_parse_addresses(b"", "A")

def test_dns_query_payload_rejects_overlong_label():
    import backend.sources.http as http

    with pytest.raises(ValueError, match="invalid DNS hostname"):
        http._dns_query_payload(("a" * 64) + ".com", "A")
