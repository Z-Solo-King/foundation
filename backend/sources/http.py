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
from ipaddress import ip_address, IPv4Address, IPv6Address
import struct
from urllib.parse import urljoin, urlparse, urlunparse

from backend.core.workers_runtime import workers_fetch

MAX_REDIRECTS = 3
MAX_BYTES = 1_000_000
DNS_OVER_HTTPS_ENDPOINTS = (
    "https://cloudflare-dns.com/dns-query",
    "https://dns.google/dns-query",
)


@dataclass(frozen=True)
class FetchResult:
    url: str
    final_url: str
    status: int
    content_type: str
    content: bytes
    etag: str | None
    redirect_chain: tuple[str, ...] = ()


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


def canonicalize_url(url: str) -> str:
    """Return the security-safe canonical URL identity used for acquisition."""
    parsed = urlparse(url)
    scheme = parsed.scheme.lower()
    if scheme not in {"http", "https"}:
        raise ValueError("only http and https URLs are allowed")
    if parsed.username or parsed.password:
        raise ValueError("userinfo in URL is not allowed")
    if not parsed.hostname or not _safe_host(parsed.hostname):
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


def validate_url(url: str) -> None:
    canonicalize_url(url)


def _dns_query_payload(hostname: str, record_type: str) -> bytes:
    """Build a bounded RFC 1035 DNS query for DoH POST without tainting the URL."""
    qtype = {"A": 1, "AAAA": 28}.get(record_type)
    if qtype is None:
        raise ValueError("unsupported DNS record type")
    host = hostname.rstrip(".")
    if not host or len(host) > 253:
        raise ValueError("invalid DNS hostname")
    try:
        ascii_host = host.encode("idna").decode("ascii")
    except UnicodeError as exc:
        raise ValueError("invalid DNS hostname") from exc
    labels = ascii_host.split(".")
    qname = b"".join(bytes((len(label),)) + label.encode("ascii") for label in labels) + b"\x00"
    return b"\x00\x00\x01\x00\x00\x01\x00\x00\x00\x00\x00\x00" + qname + struct.pack("!HH", qtype, 1)


def _dns_skip_name(payload: bytes, offset: int) -> int:
    while True:
        if offset >= len(payload):
            raise ValueError("truncated DNS response")
        length = payload[offset]
        if length == 0:
            return offset + 1
        if length & 0xC0 == 0xC0:
            if offset + 1 >= len(payload):
                raise ValueError("truncated DNS name pointer")
            return offset + 2
        if length & 0xC0:
            raise ValueError("invalid DNS label")
        offset += 1 + length
        if length > 63 or offset > len(payload):
            raise ValueError("truncated DNS label")


def _dns_parse_addresses(payload: bytes, record_type: str) -> list[str]:
    if len(payload) < 12:
        raise ValueError("truncated DNS response")
    _ident, flags, question_count, answer_count, _authority_count, _additional_count = struct.unpack("!HHHHHH", payload[:12])
    if flags & 0x000F:
        raise ValueError("DNS resolver returned an error status")
    if question_count > 64 or answer_count > 64:
        raise ValueError("DNS response exceeds answer budget")

    offset = 12
    for _ in range(question_count):
        offset = _dns_skip_name(payload, offset)
        if offset + 4 > len(payload):
            raise ValueError("truncated DNS question")
        offset += 4

    wanted_type = {"A": 1, "AAAA": 28}[record_type]
    values: list[str] = []
    for _ in range(answer_count):
        offset = _dns_skip_name(payload, offset)
        if offset + 10 > len(payload):
            raise ValueError("truncated DNS answer")
        rr_type, rr_class, _ttl, rdlength = struct.unpack("!HHIH", payload[offset:offset + 10])
        offset += 10
        if offset + rdlength > len(payload):
            raise ValueError("truncated DNS record")
        rdata = payload[offset:offset + rdlength]
        offset += rdlength
        if rr_class != 1 or rr_type != wanted_type:
            continue
        if rr_type == 1 and rdlength == 4:
            values.append(str(IPv4Address(rdata)))
        elif rr_type == 28 and rdlength == 16:
            values.append(str(IPv6Address(rdata)))
    return values


async def _doh_request(endpoint: str, encoded_query: str):
    """Send an RFC 8484 wireformat GET to a fixed, allowlisted DoH endpoint."""
    if endpoint not in DNS_OVER_HTTPS_ENDPOINTS:
        raise ValueError("unsupported DNS-over-HTTPS endpoint")
    from workers import Request, fetch

    # Keep the resolver authority fixed and encode only the DNS wire query in the
    # RFC 8484 dns query parameter. GET avoids Python Worker POST-body conversion.
    request_url = f"{endpoint}?dns={encoded_query}"
    request = Request(
        request_url,
        method="GET",
        headers={
            "Accept": "application/dns-message",
            "Cache-Control": "no-store",
        },
    )
    return await fetch(request)


async def _dns_over_https(hostname: str, record_type: str) -> list[str]:
    payload = _dns_query_payload(hostname, record_type)
    import base64

    encoded_query = base64.urlsafe_b64encode(payload).rstrip(b"=").decode("ascii")
    failures: list[str] = []
    invalid_response = False
    for endpoint in DNS_OVER_HTTPS_ENDPOINTS:
        try:
            response = await _doh_request(endpoint, encoded_query)
            if int(response.status) != 200:
                failures.append(f"{endpoint}: HTTP {int(response.status)}")
                continue
            raw = bytes(await response.arrayBuffer())
            try:
                values = _dns_parse_addresses(raw, record_type)
            except ValueError:
                invalid_response = True
                failures.append(f"{endpoint}: invalid DNS response")
                continue
            if values:
                return values
            failures.append(f"{endpoint}: no {record_type} answers")
        except Exception as exc:
            failures.append(f"{endpoint}: {type(exc).__name__}")
    detail = "; ".join(failures[:2])
    if invalid_response and all("invalid DNS response" in failure for failure in failures):
        raise RuntimeError(f"invalid DNS response for {hostname}" + (f" ({detail})" if detail else ""))
    raise RuntimeError(f"DNS resolution failed for {hostname}" + (f" ({detail})" if detail else ""))


async def _validate_public_destination(url: str, *, resolver=None) -> None:
    canonical = canonicalize_url(url)
    hostname = urlparse(canonical).hostname
    assert hostname is not None
    resolve = resolver or _dns_over_https
    addresses = []
    for record_type in ("A", "AAAA"):
        addresses.extend(await resolve(hostname, record_type))
    if not addresses:
        raise ValueError("target host did not resolve to a public address")
    try:
        unsafe = [address for address in addresses if not _safe_ip(address)]
    except ValueError as exc:
        raise ValueError("target host returned an invalid address") from exc
    if unsafe:
        raise ValueError("target host resolves to a non-public address")


async def _call_fetcher(fetcher, url: str, options: dict):
    """Call Workers Fetch with the runtime's supported signature, preserving test doubles."""
    try:
        return await fetcher(url, options)
    except TypeError as exc:
        message = str(exc)
        if "positional argument" not in message and "positional arguments" not in message:
            raise
        return await fetcher(url)


async def fetch_public_url(url: str, *, fetcher=None, dns_resolver=None) -> FetchResult:
    custom_transport = fetcher is not None
    fetcher = fetcher or _workers_fetch()
    original = canonicalize_url(url)
    current = original
    original_scheme = urlparse(original).scheme
    redirect_chain: list[str] = [original]
    for _ in range(MAX_REDIRECTS + 1):
        if not custom_transport or dns_resolver is not None:
            await _validate_public_destination(current, resolver=dns_resolver)
        else:
            current = canonicalize_url(current)
        if original_scheme == "https" and urlparse(current).scheme != "https":
            raise ValueError("https to http redirect downgrade is not allowed")
        response = await _call_fetcher(fetcher, current, {"redirect": "manual"})
        status = int(response.status)
        if status in {301, 302, 303, 307, 308}:
            location = response.headers.get("location")
            if not location:
                raise RuntimeError("redirect without Location header")
            current = canonicalize_url(urljoin(current, location))
            redirect_chain.append(current)
            continue
        content = bytes(await response.arrayBuffer())
        if len(content) > MAX_BYTES:
            raise RuntimeError("response exceeds acquisition size budget")
        return FetchResult(
            url=original,
            final_url=canonicalize_url(current),
            status=status,
            content_type=response.headers.get("content-type", "application/octet-stream"),
            content=content,
            etag=response.headers.get("etag"),
            redirect_chain=tuple(redirect_chain),
        )
    raise RuntimeError("too many redirects")
