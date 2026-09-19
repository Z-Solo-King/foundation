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


def test_workers_fetch_adapter_preserves_request_options(monkeypatch) -> None:
    import asyncio
    import sys
    import types

    captured = {}

    class FakeRequest:
        def __init__(self, url, **options):
            captured["url"] = url
            captured["options"] = options

    async def fake_fetch(request):
        captured["request"] = request
        return "response"

    fake_workers = types.SimpleNamespace(Request=FakeRequest, fetch=fake_fetch)
    monkeypatch.setitem(sys.modules, "workers", fake_workers)

    from backend.core.workers_runtime import workers_fetch

    fetcher = workers_fetch("test")
    result = asyncio.run(fetcher("https://example.com/dns-query", {
        "method": "POST",
        "headers": {"Content-Type": "application/dns-message"},
        "body": b"payload",
    }))

    assert result == "response"
    assert captured["url"] == "https://example.com/dns-query"
    assert captured["options"]["method"] == "POST"
    assert captured["options"]["headers"]["Content-Type"] == "application/dns-message"
    assert captured["options"]["body"] == b"payload"
    assert captured["request"].__class__ is FakeRequest
