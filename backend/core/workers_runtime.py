"""Cloudflare Python Workers Fetch compatibility adapter.

Use the Workers SDK for simple GET-style calls. For option-bearing calls, use the
documented JavaScript Fetch API through Python Workers FFI so POST headers and binary
request bodies reach the runtime without depending on SDK wrapper behavior.
"""

from collections.abc import Callable


def workers_fetch(context: str) -> Callable:
    """Return a bounded Worker fetch adapter with request options preserved."""
    try:
        from workers import fetch
    except ImportError as exc:
        raise RuntimeError(f"Cloudflare Workers runtime is required for {context}") from exc

    async def _fetch(url, options=None, **request_options):
        if request_options:
            merged_options = dict(options or {})
            merged_options.update(request_options)
            options = merged_options
        if not options:
            return await fetch(url)

        try:
            from js import Object, fetch as js_fetch
            from pyodide.ffi import to_js
        except ImportError:
            # Local/legacy runtime fallback: retain the Workers SDK option path.
            return await fetch(url, **dict(options))

        # Pyodide converts Python bytes/buffer values to JS TypedArrays through
        # to_js(), so binary application/dns-message POST bodies remain intact.
        js_options = to_js(dict(options), dict_converter=Object.fromEntries)
        return await js_fetch(url, js_options)

    return _fetch
