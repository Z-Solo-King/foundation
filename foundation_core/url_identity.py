import pytest

from foundation_core.url_identity import canonicalize_url, safe_host, safe_ip


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