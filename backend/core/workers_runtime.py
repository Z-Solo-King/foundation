"""Cloudflare Python Workers Fetch compatibility adapter.

The Workers Python runtime exposes Fetch through the `workers` SDK. Use its native
keyword-option interface for option-bearing requests instead of constructing a raw
JavaScript Request through Pyodide FFI; this keeps request bodies and headers in the
runtime's supported conversion path.
"""

from collections.abc import Callable


def workers_fetch(context: str) -> Callable:
    """Return a bounded Worker fetch adapter with request options preserved."""
    try:
        from workers import fetch
    except ImportError as exc:
        raise RuntimeError(f"Cloudflare Workers runtime is required for {context}") from exc

    async def _fetch(url, options=None):
        if not options:
            return await fetch(url)
        try:
            return await fetch(url, **dict(options))
        except TypeError as exc:
            # Keep a compatibility fallback for older/local SDK shims that accept
            # a Request object rather than keyword options.
            try:
                from workers import Request
            except ImportError:
                raise exc
            return await fetch(Request(url, **dict(options)))

    return _fetch
