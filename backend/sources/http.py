"""Bounded HTTP acquisition primitive for Cloudflare Python Workers.

This is a transport primitive, not a search engine. It follows only normal
public HTTP access paths, limits redirects and response size, and rejects
obvious local/private targets before fetch.
"""

from dataclasses import dataclass
from ipaddress import ip_address
from urllib.parse import urljoin, urlparse

from workers import fetch


MAX_REDIRECTS = 3
MAX_BYTES = 1_000_000


@dataclass(frozen=True)
class FetchResult:
    url: str
    final_url: str
    status: int
    content_type: str
    content: bytes
    etag: str | None


def _safe_host(hostname: str) -> bool:
    host = hostname.lower().rstrip(".")
    if host in {"localhost", "localhost.localdomain", "ip6-localhost"}:
        return False
    try:
        ip = ip_address(host)
    except ValueError:
        return True
    return not (ip.is_loopback or ip.is_private or ip.is_link_local or ip.is_reserved or ip.is_multicast)


def validate_url(url: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        raise ValueError("only http and https URLs are allowed")
    if parsed.username or parsed.password:
        raise ValueError("userinfo in URL is not allowed")
    if not parsed.hostname or not _safe_host(parsed.hostname):
        raise ValueError("target host is not allowed")
    if parsed.port is not None and parsed.port not in {80, 443}:
        raise ValueError("non-standard ports are not allowed")


async def fetch_public_url(url: str) -> FetchResult:
    validate_url(url)
    current = url
    for _ in range(MAX_REDIRECTS + 1):
        response = await fetch(current, {"redirect": "manual"})
        status = int(response.status)
        if status in {301, 302, 303, 307, 308}:
            location = response.headers.get("location")
            if not location:
                raise RuntimeError("redirect without Location header")
            # Relative Location values are normal HTTP and must be resolved
            # against the current URL before the same safety policy is applied.
            current = urljoin(current, location)
            validate_url(current)
            continue
        raw = await response.arrayBuffer()
        content = bytes(raw)
        if len(content) > MAX_BYTES:
            raise RuntimeError("response exceeds acquisition size budget")
        return FetchResult(
            url=url,
            final_url=current,
            status=status,
            content_type=response.headers.get("content-type", "application/octet-stream"),
            content=content,
            etag=response.headers.get("etag"),
        )
    raise RuntimeError("too many redirects")
