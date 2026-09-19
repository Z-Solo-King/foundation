"""Small Cloudflare Worker runtime adapter used by public transport code.

Importing the Workers runtime is intentionally lazy so deterministic code and local
unit tests can run outside a Worker runtime. Network calls with request options use
the documented Python-Workers FFI path so method, headers, body, redirects, and cache
settings reach the JavaScript Fetch API intact.
"""

from collections.abc import Callable


def workers_fetch(context: str) -> Callable:
    """Return a Worker fetch adapter with Python/JS runtime compatibility."""
    try:
        from workers import fetch
    except ImportError as exc:
        raise RuntimeError(f"Cloudflare Workers runtime is required for {context}") from exc

    async def _fetch(url, options=None):
        if not options:
            return await fetch(url)

        try:
            from js import Object, Request as JSRequest, fetch as js_fetch
            from pyodide.ffi import to_js
        except ImportError:
            # Local/unit-test fallback. In a real Python Worker the documented JS
            # FFI modules are present, so this branch is not used in production.
            try:
                from workers import Request
            except ImportError:
                return await fetch(url, options)
            try:
                return await fetch(Request(url, **options))
            except (AttributeError, TypeError):
                return await fetch(url, options)

        request_options = to_js(options, dict_converter=Object.fromEntries)
        request = JSRequest.new(url, request_options)
        return await js_fetch(request)

    return _fetch
