"""Bounded HTTP acquisition primitive for Cloudflare Python Workers.

This is a transport primitive, not a search engine. It follows only normal
public HTTP access paths, limits redirects and response size, and rejects
obvious local/private targets before fetch.

For production Worker fetches, hostname destinations are preflighted through
DNS-over-HTTPS and every returned A/AAAA address must be publicly routable.
This is defense-in-depth: the final Workers fetch still performs the actual
DNS resolution and network connection. Resolution failures fail closed.
"""

from dataclasses import dataclass
from ipaddress import ip_address
from urllib.parse import quote, urljoin, urlparse

from backend.core.workers_runtime import workers_fetch

MAX_REDIRECTS = 3
MAX_BYTES = 1_000_000
DNS_OVER_HTTPS_ENDPOINT = "https://cloudflare-dns.com/dns-query"


@dataclass(frozen=True)
class FetchResult:
    url: str
    final_url: str
    status: int
    content_type: str
    content: bytes
    etag: str | None


def _workers_fetch():
    """Compatibility shim for tests and callers that patch this adapter."""
    return workers_fetch("network acquisition")


def _safe_ip(value: str) -> bool:
    ip = ip_address(value)
    return not (ip.is_loopback or ip.is_private or ip.is_link_local or ip.is_reserved or ip.is_multicast or ip.is_unspecified)


def _safe_host(hostname: str) -> bool:
    host = hostname.lower().rstrip(".")
    if host in {"localhost", "localhost.localdomain", "ip6-localhost"}:
        return False
    try:
        return _safe_ip(host)
    except ValueError:
        return True


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


async def _dns_over_https(hostname: str, record_type: str) -> list[str]:
    fetcher = _workers_fetch()
    url = f"{DNS_OVER_HTTPS_ENDPOINT}?name={quote(hostname, safe='')}&type={record_type}"
    response = await fetcher(
        url,
        {
            "headers": {
                "Accept": "application/dns-json",
                "Cache-Control": "no-store",
            }
        },
    )
    if int(response.status) != 200:
        raise RuntimeError(f"DNS resolution failed for {hostname}")
    payload = await response.json()
    if not isinstance(payload, dict):
        raise RuntimeError(f"invalid DNS response for {hostname}")
    answers = payload.get("Answer") or ()
    values = []
    for answer in answers:
        if not isinstance(answer, dict) or int(answer.get("type", 0)) not in {1, 28}:
            continue
        value = str(answer.get("data", "")).strip()
        if value:
            values.append(value)
    return values


async def _validate_public_destination(url: str, *, resolver=None) -> None:
    validate_url(url)
    hostname = urlparse(url).hostname
    assert hostname is not None
    resolve = resolver or _dns_over_https
    addresses = []
    for record_type in ("A", "AAAA"):
        resolved = await resolve(hostname, record_type)
        addresses.extend(resolved)
    if not addresses:
        raise ValueError("target host did not resolve to a public address")
    try:
        unsafe = [address for address in addresses if not _safe_ip(address)]
    except ValueError as exc:
        raise ValueError("target host returned an invalid address") from exc
    if unsafe:
        raise ValueError("target host resolves to a non-public address")


async def fetch_public_url(url: str, *, fetcher=None, dns_resolver=None) -> FetchResult:
    custom_transport = fetcher is not None
    fetcher = fetcher or _workers_fetch()
    current = url
    for _ in range(MAX_REDIRECTS + 1):
        if not custom_transport or dns_resolver is not None:
            await _validate_public_destination(current, resolver=dns_resolver)
        else:
            validate_url(current)
        response = await fetcher(current, {"redirect": "manual"})
        status = int(response.status)
        if status in {301, 302, 303, 307, 308}:
            location = response.headers.get("location")
            if not location:
                raise RuntimeError("redirect without Location header")
            current = urljoin(current, location)
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
