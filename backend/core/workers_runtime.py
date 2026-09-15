"""Small Cloudflare Worker runtime adapter used by public transport code.

Importing ``workers.fetch`` is intentionally lazy so deterministic code and local
unit tests can run outside a Worker runtime. Callers supply a short context only
for a useful, component-specific failure message.
"""

from collections.abc import Callable


def workers_fetch(context: str) -> Callable:
    """Return Cloudflare's runtime ``fetch`` function or fail clearly."""
    try:
        from workers import fetch
    except ImportError as exc:
        raise RuntimeError(f"Cloudflare Workers runtime is required for {context}") from exc
    return fetch
