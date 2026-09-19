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
        pass

    async def fake_js_fetch(url, options):
        captured["url"] = url
        captured["options"] = options
        return "response"

    def fake_to_js(value, dict_converter=None):
        return dict_converter(value) if dict_converter else value

    monkeypatch.setitem(
        sys.modules,
        "workers",
        types.SimpleNamespace(fetch=lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("workers.fetch should not handle option-bearing production calls")
        )),
    )
    monkeypatch.setitem(
        sys.modules,
        "js",
        types.SimpleNamespace(Object=FakeObject, Request=FakeRequest, fetch=fake_js_fetch),
    )
    monkeypatch.setitem(sys.modules, "pyodide.ffi", types.SimpleNamespace(to_js=fake_to_js))

    from backend.core.workers_runtime import workers_fetch

    options = {
        "method": "POST",
        "headers": {"Content-Type": "application/dns-message"},
        "body": b"payload",
        "redirect": "manual",
    }
    result = asyncio.run(workers_fetch("test")("https://example.com/dns-query", options))

    assert result == "response"
    assert captured == {
        "url": "https://example.com/dns-query",
        "options": options,
    }


def test_workers_fetch_adapter_without_options_uses_workers_sdk(monkeypatch) -> None:
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


def test_workers_fetch_adapter_uses_sdk_fallback_when_js_ffi_is_unavailable(monkeypatch) -> None:
    import asyncio
    import builtins
    import sys
    import types

    captured = {}

    async def fake_fetch(url, **options):
        captured["url"] = url
        captured["options"] = options
        return "response"

    fake_workers = types.SimpleNamespace(fetch=fake_fetch)
    original_import = builtins.__import__

    def blocked_import(name, *args, **kwargs):
        if name == "js":
            raise ImportError("blocked")
        if name == "pyodide.ffi":
            raise ImportError("blocked")
        return original_import(name, *args, **kwargs)

    monkeypatch.setitem(sys.modules, "workers", fake_workers)
    monkeypatch.delitem(sys.modules, "js", raising=False)
    monkeypatch.delitem(sys.modules, "pyodide", raising=False)
    monkeypatch.delitem(sys.modules, "pyodide.ffi", raising=False)
    monkeypatch.setattr(builtins, "__import__", blocked_import)

    from backend.core.workers_runtime import workers_fetch

    options = {"method": "POST", "body": b"payload"}
    result = asyncio.run(workers_fetch("test")("https://example.com", options))

    assert result == "response"
    assert captured == {"url": "https://example.com", "options": options}
