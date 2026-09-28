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
    if isinstance(ip, IPv6Address):
        if (
            ip.is_loopback
            or ip.is_link_local
            or ip.is_multicast
            or ip.is_unspecified
            or ip.is_private
        ):
            return False
        if ip.packed[:2] == bytes.fromhex("2002") or ip.packed[:4] == bytes.fromhex("20010000"):
            return False
        if ip.packed[:12] == _NAT64_PREFIX:
            ip = IPv4Address(ip.packed[12:])
    if isinstance(ip, IPv4Address):
        if ip.is_loopback or ip.is_link_local or ip.is_multicast or ip.is_unspecified or ip.is_private:
            return False
    if str(ip) in _PROVIDER_DENYLIST:
        return False
    return bool(ip.is_global)


def safe_host(hostname: str) -> bool:
    host = hostname.lower().rstrip(".")
    if host in {"localhost", "localhost.localdomain", "ip6-localhost"}:
        return False
    # Reject hexadecimal-prefixed IPv4 obfuscation and bare integer/octal forms.
    # Standard dotted-decimal IPv4 remains a valid safe_ip input.
    if host.startswith("0x") and host[2:] and all(ch in "0123456789abcdef." for ch in host[2:]):
        return False
    if host and host.isdigit():
        return False
    try:
        return safe_ip(host)
    except ValueError:
        return "." in host


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
    host = parsed.hostname.lower().rstrip(".")
    host_for_netloc = f"[{host}]" if ":" in host else host
    if (
        parsed.port is None
        or (scheme == "http" and parsed.port == 80)
        or (scheme == "https" and parsed.port == 443)
    ):
        netloc = host_for_netloc
    else:
        netloc = f"{host_for_netloc}:{parsed.port}"
    path = parsed.path or "/"
    return urlunparse((scheme, netloc, path, parsed.params, parsed.query, ""))
