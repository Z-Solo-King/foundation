"""Pure URL identity and SSRF-safe host classification.

This module contains only deterministic standard-library logic. Transport,
DNS resolution and network acquisition remain outside Foundation Core.
"""

from __future__ import annotations

import re
from ipaddress import IPv4Address, IPv6Address, ip_address, ip_network
from urllib.parse import urlparse, urlunparse


_PROVIDER_DENYLIST = frozenset({"168.63.129.16"})
_NAT64_PREFIX = ip_address("64:ff9b::").packed[:12]
_NAT64_LOCAL_PREFIX = ip_network("64:ff9b:1::/48")
_SIXTOFOUR_PREFIX = ip_network("2002::/16")
_TEREDO_PREFIX = ip_network("2001:0000::/32")
_RESERVED_SUFFIXES = (".local", ".internal", ".localhost", ".home.arpa")
_NUMERIC_LABEL = re.compile(r"^(?:0[xX][0-9a-fA-F]+|0[oO][0-7]+|[0-9]+)$")


def safe_ip(value: str) -> bool:
    ip = ip_address(value)
    mapped = getattr(ip, "ipv4_mapped", None)
    if mapped is not None:
        ip = mapped

    if isinstance(ip, IPv6Address):
        if ip in _NAT64_LOCAL_PREFIX or ip in _SIXTOFOUR_PREFIX or ip in _TEREDO_PREFIX:
            return False
        if ip.packed[:12] == _NAT64_PREFIX:
            ip = IPv4Address(ip.packed[12:])

    if isinstance(ip, IPv6Address):
        if (
            ip.is_loopback
            or ip.is_link_local
            or ip.is_multicast
            or ip.is_unspecified
            or ip.is_private
            or ip.is_reserved
        ):
            return False

    if isinstance(ip, IPv4Address):
        if (
            ip.is_loopback
            or ip.is_link_local
            or ip.is_multicast
            or ip.is_unspecified
            or ip.is_private
            or ip.is_reserved
        ):
            return False

    if str(ip) in _PROVIDER_DENYLIST:
        return False
    return bool(ip.is_global)


def safe_host(hostname: str) -> bool:
    host = hostname.casefold().rstrip(".")
    if not host:
        return False
    try:
        literal = ip_address(host)
    except ValueError:
        literal = None
    if literal is not None:
        return safe_ip(host)
    if "." not in host:
        return False
    if host in {"localhost", "localhost.localdomain", "ip6-localhost"}:
        return False
    if any(host == suffix[1:] or host.endswith(suffix) for suffix in _RESERVED_SUFFIXES):
        return False

    labels = host.split(".")
    if all(_NUMERIC_LABEL.fullmatch(label) for label in labels):
        # Only canonical dotted-decimal IPv4 literals are accepted above via
        # ip_address(). Browser-style one/two/three-part, octal or hex forms
        # are rejected to keep DNS and URL identity unambiguous.
        return False

    try:
        return safe_ip(host)
    except ValueError:
        return True


def canonicalize_url(url: str) -> str:
    """Return the security-safe canonical URL identity used for acquisition."""
    parsed = urlparse(url)
    scheme = parsed.scheme.lower()
    if "://" in url:
        authority = url.split("://", 1)[1].split("/", 1)[0].split("?", 1)[0].split("#", 1)[0]
        host_part = authority.rsplit("@", 1)[-1]
        if host_part.count(":") > 1 and not host_part.startswith("["):
            raise ValueError("target host is not allowed")
    if scheme not in {"http", "https"}:
        raise ValueError("only http and https URLs are allowed")
    if parsed.username or parsed.password:
        raise ValueError("userinfo in URL is not allowed")
    if not parsed.hostname or not safe_host(parsed.hostname):
        raise ValueError("target host is not allowed")
    if parsed.port is not None and parsed.port not in {80, 443}:
        raise ValueError("non-standard ports are not allowed")
    host = parsed.hostname.casefold().rstrip(".")
    if ":" in host:
        host = f"[{host}]"
    if parsed.port is None or (scheme == "http" and parsed.port == 80) or (scheme == "https" and parsed.port == 443):
        netloc = host
    else:
        netloc = f"{host}:{parsed.port}"
    path = parsed.path or "/"
    return urlunparse((scheme, netloc, path, parsed.params, parsed.query, ""))
