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


def test_http_worker_fetch_uses_keyword_options(monkeypatch):
    import backend.sources.http as http
    calls = []

    class Response:
        status = 200
        headers = {"content-type": "text/plain", "etag": "e"}
        async def arrayBuffer(self): return b"ok"

    async def fake_fetch(url, **kwargs):
        calls.append((url, kwargs))
        return Response()

    monkeypatch.setattr(http, "_workers_fetch", lambda: fake_fetch)
    async def no_dns(*args, **kwargs):
        return None
    monkeypatch.setattr(http, "_validate_public_destination", no_dns)

    result = asyncio.run(http.fetch_public_url("https://example.com"))
    assert result.status == 200
    assert calls[-1][1] == {"redirect": "manual"}


def test_wikipedia_worker_fetch_uses_keyword_headers(monkeypatch):
    import backend.sources.wikipedia as wikipedia

    class Response:
        status = 200
        headers = {}
        async def json(self):
            return {"query": {"search": []}}

    calls = []
    async def fake_fetch(url, **kwargs):
        calls.append((url, kwargs))
        return Response()

    monkeypatch.setattr(wikipedia, "_workers_fetch", lambda: fake_fetch)
    assert asyncio.run(wikipedia.wikipedia_search("cloudflare", 1)) == []
    assert calls[-1][1] == {"headers": {"User-Agent": "ResearchIntelligenceEngine/0.1"}}
