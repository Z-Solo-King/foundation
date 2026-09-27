"""Pure URL identity and SSRF-safe host classification.

This module contains only deterministic standard-library logic. Transport,
DNS resolution and network acquisition remain outside Foundation Core.
"""
from __future__ import annotations

from ipaddress import IPv4Address, IPv6Address, ip_address
from urllib.parse import urlparse, urlunparse


_PROVIDER_DENYLIST = frozenset({"168.63.129.16"})
_NAT64_PREFIX = ip_address("64:ff9b::").packed[:12]


def safe_ip(value: str) -> bool:
    ip = ip_address(value)
    mapped = getattr(ip, "ipv4_mapped", None)
    if mapped is not None:
        ip = mapped
    if isinstance(ip, IPv6Address) and ip.packed[:12] == _NAT64_PREFIX:
        ip = IPv4Address(ip.packed[12:])
    if str(ip) in _PROVIDER_DENYLIST:
        return False
    return bool(ip.is_global)


def safe_host(hostname: str) -> bool:
    host = hostname.lower().rstrip(".")
    if host in {"localhost", "localhost.localdomain", "ip6-localhost"}:
        return False
    try:
        return safe_ip(host)
    except ValueError:
        return True


def canonicalize_url(url: str) -> str:
    """Return the security-safe canonical URL identity used for acquisition."""
    parsed = urlparse(url)
    scheme = parsed.scheme.lower()
    if scheme not in {"http", "https"}:
        raise ValueError("only http and https URLs are allowed")
    if parsed.username or parsed.password:
        raise ValueError("userinfo in URL is not allowed")
    if not parsed.hostname or not safe_host(parsed.hostname):
        raise ValueError("target host is not allowed")
    if parsed.port is not None and parsed.port not in {80, 443}:
        raise ValueError("non-standard ports are not allowed")
    host = parsed.hostname.lower().rstrip(".")
    if parsed.port is None or (scheme == "http" and parsed.port == 80) or (scheme == "https" and parsed.port == 443):
        netloc = host
    else:
        netloc = f"{host}:{parsed.port}"
    path = parsed.path or "/"
    return urlunparse((scheme, netloc, path, parsed.params, parsed.query, ""))
