import pytest

from ipaddress import ip_address

from foundation_core.url_identity import canonicalize_url, safe_host, safe_ip, _parse_obfuscated_ipv4


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        ("HTTPS://EXAMPLE.COM.:443/path#fragment", "https://example.com/path"),
        ("http://EXAMPLE.COM:80", "http://example.com/"),
        ("https://example.com", "https://example.com/"),
        ("https://example.com/a//b?x=1", "https://example.com/a//b?x=1"),
    ],
)
def test_canonicalize_url_preserves_security_safe_identity(source, expected):
    assert canonicalize_url(source) == expected


@pytest.mark.parametrize(
    "source",
    [
        "ftp://example.com",
        "https://user:pass@example.com",
        "https://127.0.0.1",
        "https://100.64.0.1",
        "https://[64:ff9b::127.0.0.1]",
        "https://example.com:8443",
        "https://",
        "not-a-url",
        "http://0x7f.1/",
        "http://017700000001/",
        "http://2130706433/",
        "http://64:ff9b::224.0.0.1/",
        "http://ff02::1/",
    ],
)
def test_canonicalize_url_rejects_unsafe_forms(source):
    with pytest.raises(ValueError):
        canonicalize_url(source)


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("8.8.8.8", True),
        ("::ffff:8.8.8.8", True),
        ("100.64.0.1", False),
        ("168.63.129.16", False),
        ("64:ff9b::127.0.0.1", False),
        ("64:ff9b::224.0.0.1", False),
        ("ff02::1", False),
    ],
)
def test_safe_ip_keeps_shared_and_provider_ranges_blocked(value, expected):
    assert safe_ip(value) is expected


def test_safe_host_handles_domains_and_localhost():
    assert safe_host("LOCALHOST") is False
    assert safe_host("localhost.localdomain") is False
    assert safe_host("example.com") is True


def test_safe_ip_covers_public_ipv6_and_nat64_public_ipv4():
    assert safe_ip("2001:4860:4860::8888") is True
    assert safe_ip("64:ff9b::8.8.8.8") is True


def test_safe_host_rejects_numeric_obfuscation_but_allows_ipv4_domains():
    assert safe_host("1.1.1.1") is True
    assert safe_host("2130706433") is False
    assert safe_host("0x7f.1") is False


def test_canonicalize_url_rejects_ipv6_multicast_and_nat64_multicast():
    for source in ("http://[ff02::1]/", "http://[64:ff9b::224.0.0.1]/"):
        with pytest.raises(ValueError):
            canonicalize_url(source)


@pytest.mark.parametrize(
    "source",
    [
        "http://127.1/",
        "http://0177.0.0.1/",
        "http://0x7f.0x0.0x0.0x1/",
        "http://0x7f.1/",
        "http://2130706433/",
        "http://intranet/",
        "http://service.internal/",
        "http://printer.local/",
        "http://host.home.arpa/",
        "http://[2002:7f00:0001::1]/",
        "http://[2001:0000:7f00:0001::1]/",
        "http://[64:ff9b:1::1]/",
    ],
)
def test_canonicalize_url_rejects_browser_numeric_private_and_reserved_forms(source):
    with pytest.raises(ValueError):
        canonicalize_url(source)


def test_canonicalize_url_preserves_brackets_for_public_ipv6():
    assert canonicalize_url("https://[2001:4860:4860::8888]/x") == "https://[2001:4860:4860::8888]/x"


def test_safe_host_rejects_single_label_and_reserved_suffixes():
    assert safe_host("intranet") is False
    assert safe_host("example.local") is False
    assert safe_host("example.internal") is False
    assert safe_host("example.localhost") is False
    assert safe_host("example.home.arpa") is False


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        ("127.1", False),
        ("0177.0.0.1", False),
        ("0x7f.1", False),
        ("1.1.1.1", True),
        ("8.8.8.8", True),
    ],
)
def test_safe_host_classifies_numeric_ipv4_forms_before_dns(source, expected):
    assert safe_host(source) is expected


def test_safe_host_rejects_empty_hostname():
    assert safe_host("") is False


def test_obfuscated_ipv4_supports_explicit_hex_and_octal_parts():
    assert safe_host("0x8.0o8.0o0.0o1") is True


def test_obfuscated_ipv4_rejects_invalid_octal_parts():
    assert safe_host("09.0.0.1") is False


def test_obfuscated_ipv4_rejects_out_of_range_parts():
    assert safe_host("256.1.1.1") is False


def test_obfuscated_ipv4_forms_are_parsed_but_rejected_by_safe_host():
    assert _parse_obfuscated_ipv4("134744072") == ip_address("8.8.8.8")
    assert _parse_obfuscated_ipv4("8.1") == ip_address("8.0.0.1")
    assert _parse_obfuscated_ipv4("8.8.1") == ip_address("8.8.0.1")
    assert safe_host("134744072") is False
    assert safe_host("8.1") is True
    assert safe_host("8.8.1") is False
