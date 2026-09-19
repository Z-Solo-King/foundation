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


def test_workers_fetch_adapter_passes_options_to_native_sdk(monkeypatch) -> None:
    import asyncio
    import sys
    import types

    captured = {}

    async def fake_fetch(url, **options):
        captured["url"] = url
        captured["options"] = options
        return "response"

    monkeypatch.setitem(sys.modules, "workers", types.SimpleNamespace(fetch=fake_fetch))

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


def test_workers_fetch_adapter_without_options_uses_native_sdk(monkeypatch) -> None:
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


def test_workers_fetch_adapter_falls_back_to_request_for_legacy_sdk(monkeypatch) -> None:
    import asyncio
    import sys
    import types

    captured = {}

    class FakeRequest:
        def __init__(self, url, **options):
            self.url = url
            self.options = options

    async def fake_fetch(*args, **kwargs):
        if kwargs:
            raise TypeError("legacy fetch does not accept keyword options")
        captured["request"] = args[0]
        return "response"

    monkeypatch.setitem(sys.modules, "workers", types.SimpleNamespace(fetch=fake_fetch, Request=FakeRequest))

    from backend.core.workers_runtime import workers_fetch

    options = {"method": "POST", "body": b"payload"}
    result = asyncio.run(workers_fetch("test")("https://example.com", options))

    assert result == "response"
    assert captured["request"].url == "https://example.com"
    assert captured["request"].options == options
