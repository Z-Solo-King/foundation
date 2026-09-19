"""Small Cloudflare Worker runtime adapter used by public transport code.

Importing workers.fetch is intentionally lazy so deterministic code and local
unit tests can run outside a Worker runtime. Callers supply a short context only
for a useful, component-specific failure message.
"""

from collections.abc import Callable


def workers_fetch(context: str) -> Callable:
    """Return a Worker fetch adapter with Python SDK request compatibility."""
    try:
        from workers import Request, fetch
    except ImportError as exc:
        raise RuntimeError(f"Cloudflare Workers runtime is required for {context}") from exc

    async def _fetch(url, options=None):
        if options:
            return await fetch(Request(url, **options))
        return await fetch(url)

    return _fetch
