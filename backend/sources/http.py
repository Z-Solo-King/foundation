"""Bounded HTTP acquisition primitive for Cloudflare Python Workers.

This is a transport primitive, not a search engine. It follows only normal
public HTTP access paths, limits redirects and response size, and rejects
obvious local/private targets before fetch.

For production Worker fetches, hostname destinations are preflighted through
DNS-over-HTTPS and every returned A/AAAA address must be publicly routable.
This is defense-in-depth: the final Workers fetch still performs the actual
DNS resolution and network connection. Resolution failures fail closed.
"""

import asyncio
from dataclasses import dataclass
from ipaddress import IPv4Address, IPv6Address
import struct
from urllib.parse import urljoin, urlparse, urlunparse

from backend.core.workers_runtime import workers_fetch
from foundation_core.url_identity import canonicalize_url, safe_host as _safe_host, safe_ip as _safe_ip

MAX_REDIRECTS = 3
MAX_BYTES = 1_000_000
FETCH_DEADLINE_SECONDS = 15.0
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


def _response_bytes(value) -> bytes:
    """Convert a Workers/Pyodide buffer proxy into native Python bytes."""
    if isinstance(value, bytes):
        return value
    if isinstance(value, bytearray):
        return bytes(value)
    if isinstance(value, memoryview):
        return value.tobytes()

    # Cloudflare's Python Workers runtime may return a Pyodide JsProxy for
    # Response.bytes(). ArrayBuffer/TypedArray proxies are explicitly
    # convertible through to_py(), which yields a Python memoryview.
    to_py = getattr(value, "to_py", None)
    if callable(to_py):
        converted = to_py()
        if isinstance(converted, bytes):
            return converted
        if isinstance(converted, bytearray):
            return bytes(converted)
        if isinstance(converted, memoryview):
            return converted.tobytes()
        to_bytes = getattr(converted, "tobytes", None)
        if callable(to_bytes):
            result = to_bytes()
            if isinstance(result, bytes):
                return result

    to_bytes = getattr(value, "to_bytes", None)
    if callable(to_bytes):
        converted = to_bytes()
        if isinstance(converted, bytes):
            return converted
        if isinstance(converted, bytearray):
            return bytes(converted)
        if isinstance(converted, memoryview):
            return converted.tobytes()
        nested_to_py = getattr(converted, "to_py", None)
        if callable(nested_to_py):
            converted = nested_to_py()
            if isinstance(converted, memoryview):
                return converted.tobytes()
            if isinstance(converted, (bytes, bytearray)):
                return bytes(converted)

    return bytes(value)


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
    """Send an RFC 8484 wireformat GET through the JS Fetch API."""
    if endpoint not in DNS_OVER_HTTPS_ENDPOINTS:
        raise ValueError("unsupported DNS-over-HTTPS endpoint")
    request_url = f"{endpoint}?dns={encoded_query}"
    # Reuse the runtime adapter's option-bearing path. It enters the native
    # JavaScript Fetch API with a URL string, avoiding Python Workers Response
    # wrappers whose bytes() bridge is not reliable in the deployed runtime.
    fetcher = _workers_fetch()
    return await fetcher(
        request_url,
        {
            "headers": {
                "Accept": "application/dns-message",
                "Cache-Control": "no-store",
            }
        },
    )


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
            raw = _response_bytes(await response.arrayBuffer())
            try:
                values = _dns_parse_addresses(raw, record_type)
            except ValueError:
                invalid_response = True
                failures.append(f"{endpoint}: invalid DNS response")
                continue
        except Exception as exc:
            detail = str(exc).strip()
            if len(detail) > 240:
                detail = detail[:240]
            suffix = f": {detail}" if detail else ""
            failures.append(f"{endpoint}: {type(exc).__name__}{suffix}")
            continue
        if values:
            return values
        failures.append(f"{endpoint}: no {record_type} answers")
        break
    detail = "; ".join(failures[:2])
    if any("no A answers" in failure or "no AAAA answers" in failure for failure in failures):
        raise RuntimeError(f"DNS resolution failed for {hostname}" + (f" ({detail})" if detail else ""))
    if invalid_response and all("invalid DNS response" in failure for failure in failures):
        raise RuntimeError(f"invalid DNS response for {hostname}" + (f" ({detail})" if detail else ""))
    raise RuntimeError(f"DNS resolution failed for {hostname}" + (f" ({detail})" if detail else ""))


async def _validate_public_destination(url: str, *, resolver=None) -> None:
    canonical = canonicalize_url(url)
    hostname = urlparse(canonical).hostname
    if not hostname:
        raise ValueError("target host is missing")
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
    """Call the transport while preserving redirect policy in production."""
    try:
        return await fetcher(url, options)
    except TypeError as exc:
        from backend.core.workers_runtime import WorkersFetchAdapter
        if isinstance(fetcher, WorkersFetchAdapter):
            raise RuntimeError("worker fetch adapter rejected request options") from exc
        message = str(exc)
        if "positional argument" not in message and "positional arguments" not in message:
            raise
        return await fetcher(url)


def _remaining_deadline(started: float) -> float:
    remaining = FETCH_DEADLINE_SECONDS - (asyncio.get_running_loop().time() - started)
    if remaining <= 0:
        raise RuntimeError("source acquisition deadline exceeded")
    return remaining


def _declared_content_length(headers) -> int | None:
    value = headers.get("content-length")
    if value is None:
        return None
    try:
        declared = int(str(value).strip())
    except (TypeError, ValueError):
        return None
    return declared


async def _resolve_public_host(hostname: str, resolver, cache: dict[str, tuple[str, ...]], timeout: float) -> None:
    if hostname in cache:
        return
    addresses: list[str] = []
    for record_type in ("A", "AAAA"):
        addresses.extend(await asyncio.wait_for(resolver(hostname, record_type), timeout=timeout))
    if not addresses:
        raise ValueError("target host did not resolve to a public address")
    try:
        unsafe = [address for address in addresses if not _safe_ip(address)]
    except ValueError as exc:
        raise ValueError("target host returned an invalid address") from exc
    if unsafe:
        raise ValueError("target host resolves to a non-public address")
    cache[hostname] = tuple(addresses)


async def _fetch_response_with_deadline(fetcher, url: str, options: dict, timeout: float):
    try:
        return await asyncio.wait_for(_call_fetcher(fetcher, url, options), timeout=timeout)
    except asyncio.TimeoutError as exc:
        raise RuntimeError("source fetch timed out") from exc


async def _read_body_with_deadline(response, timeout: float) -> bytes:
    try:
        return _response_bytes(await asyncio.wait_for(response.arrayBuffer(), timeout=timeout))
    except asyncio.TimeoutError as exc:
        raise RuntimeError("source body read timed out") from exc


async def fetch_public_url(url: str, *, fetcher=None, dns_resolver=None) -> FetchResult:
    custom_transport = fetcher is not None
    fetcher = fetcher or _workers_fetch()
    original = canonicalize_url(url)
    current = original
    original_scheme = urlparse(original).scheme
    redirect_chain: list[str] = [original]
    started = asyncio.get_running_loop().time()
    dns_cache: dict[str, tuple[str, ...]] = {}

    for _ in range(MAX_REDIRECTS + 1):
        remaining = _remaining_deadline(started)
        if not custom_transport or dns_resolver is not None:
            hostname = urlparse(current).hostname
            if not hostname:
                raise ValueError("target host is missing")
            await _resolve_public_host(
                hostname,
                dns_resolver or _dns_over_https,
                dns_cache,
                remaining,
            )
        else:
            current = canonicalize_url(current)
        if original_scheme == "https" and urlparse(current).scheme != "https":
            raise ValueError("https to http redirect downgrade is not allowed")

        response = await _fetch_response_with_deadline(
            fetcher, current, {"redirect": "manual"}, _remaining_deadline(started)
        )
        status = int(response.status)
        if status in {301, 302, 303, 307, 308}:
            location = response.headers.get("location")
            if not location:
                raise RuntimeError("redirect without Location header")
            current = canonicalize_url(urljoin(current, location))
            redirect_chain.append(current)
            continue

        declared_length = _declared_content_length(response.headers)
        if declared_length is not None and (declared_length < 0 or declared_length > MAX_BYTES):
            raise RuntimeError("response exceeds acquisition size budget")
        content = await _read_body_with_deadline(response, _remaining_deadline(started))
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
