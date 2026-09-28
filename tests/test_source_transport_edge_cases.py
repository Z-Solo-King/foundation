import asyncio
import builtins
import sys
import types
from types import SimpleNamespace
import pytest


def test_source_transport_and_wikipedia_boundaries(monkeypatch):
    import backend.sources.http as http
    import backend.sources.wikipedia as wikipedia
    assert http._safe_host("example.com") is True and http._safe_host("127.0.0.1") is False
    with pytest.raises(RuntimeError):
        monkeypatch.setattr(http, "_workers_fetch", lambda: (_ for _ in ()).throw(RuntimeError("runtime")))
        asyncio.run(http.fetch_public_url("https://example.com"))
    class Resp:
        def __init__(self,status=200,headers=None,body=b"ok"): self.status=status; self.headers=headers or {}; self.body=body
        async def arrayBuffer(self): return self.body
        async def json(self): return {}
    async def fetcher(url, opts): return Resp()
    assert asyncio.run(http.fetch_public_url("https://example.com", fetcher=fetcher)).status == 200
    redirects = iter([Resp(302,{"location":"/x"}), Resp(200,{},b"x")])
    async def nxt(_u,_o): return next(redirects)
    result = asyncio.run(http.fetch_public_url("https://example.com", fetcher=nxt))
    assert result.final_url.endswith("/x")
    assert result.redirect_chain == ("https://example.com/", "https://example.com/x")
    async def bad_redirect(_u,_o): return Resp(302,{})
    with pytest.raises(RuntimeError): asyncio.run(http.fetch_public_url("https://example.com", fetcher=bad_redirect))
    async def huge(_u,_o): return Resp(200,{},b"x"*(http.MAX_BYTES+1))
    with pytest.raises(RuntimeError): asyncio.run(http.fetch_public_url("https://example.com", fetcher=huge))
    async def wiki(_u,_o): return Resp(200,{},b"")
    monkeypatch.setattr(wikipedia,"_workers_fetch",lambda: wiki)
    assert asyncio.run(wikipedia._implementation("q",2,fetcher=wiki)) == []


def test_http_and_wikipedia_runtime_paths(monkeypatch):
    import backend.sources.http as http
    import backend.sources.wikipedia as wikipedia
    assert http._safe_host("localhost") is False
    assert http._safe_host("1.1.1.1") is True
    assert http._safe_host("192.168.1.1") is False
    assert http._safe_host("not-an-ip.example") is True
    with pytest.raises(ValueError): http.validate_url("ftp://example.com")
    with pytest.raises(ValueError): http.validate_url("https://user:pass@example.com")
    with pytest.raises(ValueError): http.validate_url("https://example.com:8443")
    with pytest.raises(ValueError): http.validate_url("http://localhost")
    original_import = builtins.__import__
    def blocked_import(name,*args,**kwargs):
        if name == "workers": raise ImportError("blocked")
        return original_import(name,*args,**kwargs)
    monkeypatch.setattr(builtins,"__import__",blocked_import)
    with pytest.raises(RuntimeError,match="runtime"): http._workers_fetch()
    with pytest.raises(RuntimeError,match="runtime"): wikipedia._workers_fetch()


def test_http_runtime_error_and_redirect_exhaustion(monkeypatch):
    import backend.sources.http as http
    monkeypatch.delitem(sys.modules,"workers",raising=False)
    with pytest.raises(RuntimeError,match="Cloudflare Workers runtime"): http._workers_fetch()
    class Response:
        status=302; headers={"location":"https://example.com/next"}
        async def arrayBuffer(self): return b""
    async def fetcher(_url,_opts): return Response()
    with pytest.raises(RuntimeError,match="too many redirects"): asyncio.run(http.fetch_public_url("https://example.com",fetcher=fetcher))


def test_http_runtime_export_and_redirect_without_location(monkeypatch):
    import backend.sources.http as http
    monkeypatch.setitem(sys.modules,"workers",types.SimpleNamespace(fetch=lambda *_args,**_kwargs: object()))
    assert http._workers_fetch() is not None
    monkeypatch.delitem(sys.modules,"workers",raising=False)
    with pytest.raises(RuntimeError): http._workers_fetch()
    class Response:
        status=302; headers={}
        async def arrayBuffer(self): return b""
    async def fetcher(_url,_opts): return Response()
    with pytest.raises(RuntimeError,match="redirect"): asyncio.run(http.fetch_public_url("https://example.com",fetcher=fetcher))


def test_http_success_transport_and_wikipedia_worker_export(monkeypatch):
    import backend.sources.http as http
    import backend.sources.wikipedia as wikipedia
    class Response:
        status=200; headers={"content-type":"text/plain","etag":"etag-1"}
        async def arrayBuffer(self): return b"hello"
    async def fetcher(_url,_opts): return Response()
    result=asyncio.run(http.fetch_public_url("https://example.com",fetcher=fetcher)); assert result.status==200 and result.content==b"hello" and result.etag=="etag-1"
    fake_workers=SimpleNamespace(fetch=lambda *_args,**_kwargs: None); monkeypatch.setitem(sys.modules,"workers",fake_workers); assert callable(wikipedia._workers_fetch())


def test_dns_preflight_rejects_private_addresses_and_allows_public(monkeypatch):
    import backend.sources.http as http

    async def resolver(hostname, record_type):
        assert hostname == "example.com"
        return ["192.168.1.10"] if record_type == "A" else []

    async def fetcher(_url, _opts):
        raise AssertionError("private target must be rejected before transport")

    with pytest.raises(ValueError, match="non-public"):
        asyncio.run(http.fetch_public_url("https://example.com", fetcher=fetcher, dns_resolver=resolver))

    async def public_resolver(_hostname, record_type):
        return ["93.184.216.34"] if record_type == "A" else []

    class Response:
        status = 200
        headers = {}

        async def arrayBuffer(self):
            return b"ok"

    async def good_fetcher(_url, _opts):
        return Response()

    result = asyncio.run(http.fetch_public_url("https://example.com", fetcher=good_fetcher, dns_resolver=public_resolver))
    assert result.status == 200


def test_dns_preflight_rechecks_each_redirect(monkeypatch):
    import backend.sources.http as http
    redirects = iter([
        SimpleNamespace(status=302, headers={"location": "https://internal.example/next"}),
    ])

    async def fetcher(_url, _opts):
        return next(redirects)

    async def resolver(hostname, record_type):
        if hostname == "example.com":
            return ["93.184.216.34"] if record_type == "A" else []
        return ["10.0.0.8"] if record_type == "A" else []

    with pytest.raises(ValueError, match="non-public"):
        asyncio.run(http.fetch_public_url("https://example.com", fetcher=fetcher, dns_resolver=resolver))


def test_fetch_public_url_supports_workers_single_argument_fetch():
    import backend.sources.http as http

    class Response:
        status = 200
        headers = {"content-type": "text/plain"}

        async def arrayBuffer(self):
            return b"ok"

    calls = []
    async def fetcher(url):
        calls.append(url)
        return Response()

    result = asyncio.run(http.fetch_public_url("https://example.com", fetcher=fetcher))
    assert result.status == 200
    assert calls == ["https://example.com/"]




def test_fetch_public_url_reraises_unrelated_type_error():
    import backend.sources.http as http

    async def broken(_url, _opts):
        raise TypeError("internal bug")

    with pytest.raises(TypeError, match="internal bug"):
        asyncio.run(http.fetch_public_url("https://example.com", fetcher=broken))




def test_wikipedia_search_supports_workers_single_argument_fetch():
    import backend.sources.wikipedia as wikipedia

    class Response:
        status = 200

        async def json(self):
            return {"query": {"search": []}}

    calls = []

    async def fetcher(url):
        calls.append(url)
        return Response()

    assert asyncio.run(wikipedia._implementation("q", 2, fetcher=fetcher)) == []
    assert calls and "w/api.php" in calls[0]


@pytest.mark.parametrize("declared_length", [1_000_001, -1])
def test_fetch_public_url_rejects_invalid_or_oversized_declared_length(monkeypatch, declared_length):
    import backend.sources.http as http

    class Response:
        status = 200
        headers = {"content-length": str(declared_length)}

        async def arrayBuffer(self):
            raise AssertionError("oversized or negative declarations must be rejected before reading")

    async def fetcher(_url, _opts):
        return Response()

    with pytest.raises(RuntimeError, match="size budget"):
        asyncio.run(http.fetch_public_url("https://example.com", fetcher=fetcher))


def test_fetch_public_url_ignores_malformed_content_length_and_reads_body():
    import backend.sources.http as http

    class Response:
        status = 200
        headers = {"content-length": "not-a-number", "content-type": "text/plain"}

        async def arrayBuffer(self):
            return b"ok"

    async def fetcher(_url, _opts):
        return Response()

    result = asyncio.run(http.fetch_public_url("https://example.com", fetcher=fetcher))
    assert result.content == b"ok"


def test_fetch_public_url_uses_total_deadline_for_fetch_and_body(monkeypatch):
    import backend.sources.http as http

    monkeypatch.setattr(http, "FETCH_DEADLINE_SECONDS", 0.01)

    class Response:
        status = 200
        headers = {}

        async def arrayBuffer(self):
            await asyncio.sleep(0.05)
            return b"late"

    async def slow_fetcher(_url, _opts):
        await asyncio.sleep(0.05)
        return Response()

    with pytest.raises(RuntimeError, match="timed out"):
        asyncio.run(http.fetch_public_url("https://example.com", fetcher=slow_fetcher))


def test_fetch_public_url_caches_dns_per_host_across_redirects():
    import backend.sources.http as http

    responses = iter([
        type("Response", (), {
            "status": 302,
            "headers": {"location": "/next"},
            "arrayBuffer": lambda self: None,
        })(),
        type("Response", (), {
            "status": 200,
            "headers": {"content-type": "text/plain"},
            "arrayBuffer": lambda self: None,
        })(),
    ])

    async def fetcher(_url, _opts):
        response = next(responses)
        async def array_buffer():
            return b"ok"
        response.arrayBuffer = array_buffer
        return response

    calls = []

    async def resolver(hostname, record_type):
        calls.append((hostname, record_type))
        return ["93.184.216.34"] if record_type == "A" else []

    result = asyncio.run(
        http.fetch_public_url(
            "https://example.com",
            fetcher=fetcher,
            dns_resolver=resolver,
        )
    )
    assert result.status == 200
    assert calls == [("example.com", "A"), ("example.com", "AAAA")]


def test_call_fetcher_never_drops_production_redirect_options():
    import backend.sources.http as http
    from backend.core.workers_runtime import WorkersFetchAdapter

    async def legacy_fetch(url):
        return object()

    adapter = WorkersFetchAdapter("test", legacy_fetch)
    with pytest.raises(RuntimeError, match="request options"):
        asyncio.run(http._call_fetcher(adapter, "https://example.com/", {"redirect": "manual"}))


def test_public_destination_rejects_missing_hostname(monkeypatch):
    import backend.sources.http as http

    monkeypatch.setattr(http, "canonicalize_url", lambda _url: "http:///missing-host")
    with pytest.raises(ValueError, match="target host is missing"):
        asyncio.run(http._validate_public_destination("https://example.com", resolver=lambda *_args: []))


def test_fetch_public_url_deadline_expires_before_transport(monkeypatch):
    import backend.sources.http as http

    monkeypatch.setattr(http, "FETCH_DEADLINE_SECONDS", -1)

    async def fetcher(_url, _opts):
        raise AssertionError("transport must not start after the deadline")

    with pytest.raises(RuntimeError, match="deadline exceeded"):
        asyncio.run(http.fetch_public_url("https://example.com", fetcher=fetcher))


def test_fetch_public_url_body_read_timeout(monkeypatch):
    import backend.sources.http as http

    monkeypatch.setattr(http, "FETCH_DEADLINE_SECONDS", 0.05)

    class Response:
        status = 200
        headers = {}

        async def arrayBuffer(self):
            await asyncio.sleep(0.2)
            return b"late"

    async def fast_fetcher(_url, _opts):
        return Response()

    with pytest.raises(RuntimeError, match="body read timed out"):
        asyncio.run(http.fetch_public_url("https://example.com", fetcher=fast_fetcher))


def test_fetch_public_url_rejects_invalid_resolved_address_before_transport():
    import backend.sources.http as http

    async def resolver(_hostname, _record_type):
        return ["not-an-ip"]

    async def fetcher(_url, _opts):
        raise AssertionError("invalid DNS address must be rejected")

    with pytest.raises(ValueError, match="invalid address"):
        asyncio.run(
            http.fetch_public_url(
                "https://example.com",
                fetcher=fetcher,
                dns_resolver=resolver,
            )
        )


def test_fetch_public_url_rejects_missing_hostname_before_transport(monkeypatch):
    import backend.sources.http as http

    monkeypatch.setattr(http, "canonicalize_url", lambda _url: "http:///missing-host")

    async def fetcher(_url, _opts):
        raise AssertionError("missing hostname must be rejected")

    with pytest.raises(ValueError, match="target host is missing"):
        asyncio.run(http.fetch_public_url("https://example.com", fetcher=fetcher, dns_resolver=lambda *_args: []))


def test_resolve_public_host_rejects_empty_address_set():
    import backend.sources.http as http

    async def resolver(_hostname, _record_type):
        return []

    with pytest.raises(ValueError, match="did not resolve"):
        asyncio.run(
            http._resolve_public_host(
                "example.com",
                resolver,
                {},
                1.0,
            )
        )


def test_resolve_public_host_rejects_private_address_set():
    import backend.sources.http as http

    async def resolver(_hostname, _record_type):
        return ["10.0.0.1"] if _record_type == "A" else []

    with pytest.raises(ValueError, match="non-public"):
        asyncio.run(
            http._resolve_public_host(
                "example.com",
                resolver,
                {},
                1.0,
            )
        )
