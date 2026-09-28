import pytest

from foundation_core.url_identity import canonicalize_url, safe_host, safe_ip

@pytest.mark.parametrize(("source", "expected"), [
    ("HTTPS://EXAMPLE.COM.:443/path#fragment", "https://example.com/path"),
    ("http://EXAMPLE.COM:80", "http://example.com/"),
    ("https://example.com", "https://example.com/"),
    ("https://[2001:4860:4860::8888]/path", "https://[2001:4860:4860::8888]/path"),
])
def test_canonicalize_url_preserves_safe_identity(source, expected):
    assert canonicalize_url(source) == expected

@pytest.mark.parametrize("source", [
    "https://127.0.0.1", "https://100.64.0.1", "https://2130706433/",
    "http://0x7f.1/", "http://017.000.000.001/", "http://1.2/",
    "http://intranet/", "http://service.internal/", "http://ff02::1/",
    "http://[2002:c000:0204::1]/", "http://[2001:0000:4136:e378:8000:63bf:3fff:fdd2]/",
])
def test_canonicalize_url_rejects_ambiguous_or_non_public_targets(source):
    with pytest.raises(ValueError):
        canonicalize_url(source)

@pytest.mark.parametrize(("value", "expected"), [
    ("8.8.8.8", True), ("::ffff:8.8.8.8", True), ("100.64.0.1", False),
    ("168.63.129.16", False), ("64:ff9b::127.0.0.1", False), ("ff02::1", False),
    ("2002:c000:0204::1", False), ("2001:0000:4136:e378:8000:63bf:3fff:fdd2", False),
])
def test_safe_ip_keeps_private_provider_and_transition_ranges_blocked(value, expected):
    assert safe_ip(value) is expected

def test_safe_host_handles_domain_and_internal_name_policy():
    assert safe_host("LOCALHOST") is False
    assert safe_host("example.com") is True
    assert safe_host("intranet") is False
    assert safe_host("service.internal") is False

def test_safe_ip_accepts_public_ipv6_and_public_nat64_mapping():
    assert safe_ip("2001:4860:4860::8888") is True
    assert safe_ip("64:ff9b::8.8.8.8") is True

def test_safe_host_rejects_numeric_obfuscation_but_allows_normal_labels():
    assert safe_host("1.1.1.1") is True
    assert safe_host("2130706433") is False
    assert safe_host("0x7f.1") is False
    assert safe_host("123.example.com") is True
