import pytest
from foundation_core.url_identity import canonicalize_url, safe_ip


def test_public_ipv6_is_canonicalized_with_brackets():
    assert canonicalize_url("https://[2001:4860:4860::8888]/x") == "https://[2001:4860:4860::8888]/x"


@pytest.mark.parametrize("source", [
    "http://[2002:c000:0204::1]/",
    "http://[2001:0000:4136:e378:8000:63bf:3fff:fdd2]/",
])
def test_ipv6_transition_ranges_are_blocked(source):
    with pytest.raises(ValueError):
        canonicalize_url(source)
