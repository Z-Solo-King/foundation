import pytest

from backend.core.workers_runtime import workers_fetch
from foundation_core.normalization import canonical_url


def test_canonical_url_normalizes_scheme_host_port_and_path() -> None:
    assert canonical_url(" HTTPS://Example.COM:443/path?q=1#fragment ") == "https://example.com/path?q=1"
    assert canonical_url("http://Example.COM:8080") == "http://example.com:8080/"


def test_canonical_url_rejects_non_http_absolute_urls() -> None:
    with pytest.raises(ValueError, match=r"source URL must be absolute HTTP\(S\)"):
        canonical_url("relative/path")


def test_canonical_url_allows_component_specific_error_text() -> None:
    with pytest.raises(ValueError, match="unsupported URL: 'file:///tmp/test'"):
        canonical_url("file:///tmp/test", error_message="unsupported URL: 'file:///tmp/test'")


def test_workers_fetch_is_lazy_and_reports_context() -> None:
    with pytest.raises(RuntimeError, match="Cloudflare Workers runtime is required for unit-test"):
        workers_fetch("unit-test")


def test_workers_fetch_adapter_uses_js_fetch_for_request_options(monkeypatch) -> None:
    import asyncio
    import sys
    import types

    captured = {}

    class FakeObject:
        @staticmethod
        def fromEntries(value):
            return value

    class FakeRequest:
        @classmethod
        def new(cls, url, options):
            captured["url"] = url
            captured["options"] = options
            return (url, options)

    async def fake_js_fetch(request):
        captured["request"] = request
        return "response"

    def fake_to_js(value, dict_converter=None):
        return dict_converter(value) if dict_converter else value

    class FakeWorkers:
        @staticmethod
        async def fetch(*_args, **_kwargs):
            raise AssertionError("workers.fetch should not carry request options in production path")

    monkeypatch.setitem(sys.modules, "workers", FakeWorkers)
    monkeypatch.setitem(sys.modules, "js", types.SimpleNamespace(Object=FakeObject, Request=FakeRequest, fetch=fake_js_fetch))
    monkeypatch.setitem(sys.modules, "pyodide", types.SimpleNamespace())
    monkeypatch.setitem(sys.modules, "pyodide.ffi", types.SimpleNamespace(to_js=fake_to_js))

    from backend.core.workers_runtime import workers_fetch

    options = {"method": "POST", "headers": {"Content-Type": "application/dns-message"}, "body": b"payload"}
    result = asyncio.run(workers_fetch("test")("https://example.com/dns-query", options))

    assert result == "response"
    assert captured["url"] == "https://example.com/dns-query"
    assert captured["options"] is options
    assert captured["request"] == (captured["url"], options)


def test_workers_fetch_adapter_without_options_uses_workers_fetch(monkeypatch) -> None:
    import asyncio
    import sys
    import types

    calls = []

    async def fake_fetch(url):
        calls.append(url)
        return "response"

    monkeypatch.setitem(sys.modules, "workers", types.SimpleNamespace(fetch=fake_fetch))

    from backend.core.workers_runtime import workers_fetch

    result = asyncio.run(workers_fetch("test")("https://example.com"))
    assert result == "response"
    assert calls == ["https://example.com"]


