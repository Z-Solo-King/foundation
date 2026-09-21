"""Cloudflare Python Workers Fetch compatibility adapter.

Use the Workers SDK for simple GET-style calls. For option-bearing calls, use the
documented JavaScript Fetch API through Python Workers FFI so POST headers and binary
request bodies reach the runtime without depending on SDK wrapper behavior.
"""

from dataclasses import dataclass
from enum import StrEnum
from typing import Any

MAX_CONTEXT_LENGTH = 160


class FetchTransport(StrEnum):
    WORKERS_SDK = "workers_sdk"
    JS_FETCH_FFI = "js_fetch_ffi"
    WORKERS_SDK_FALLBACK = "workers_sdk_fallback"


@dataclass(frozen=True)
class RuntimeCapabilityReceipt:
    """Non-authoritative receipt of the actual transport path used for one fetch."""

    schema: str
    context: str
    transport: FetchTransport
    options_present: bool
    fallback_used: bool

    def __post_init__(self) -> None:
        if self.schema != "workers-runtime-capability/v1":
            raise ValueError("unsupported runtime capability schema")
        if not self.context.strip() or len(self.context) > MAX_CONTEXT_LENGTH:
            raise ValueError("runtime capability context is invalid")
        if not isinstance(self.options_present, bool) or not isinstance(self.fallback_used, bool):
            raise ValueError("runtime capability flags must be boolean")
        if self.fallback_used != (self.transport is FetchTransport.WORKERS_SDK_FALLBACK):
            raise ValueError("runtime capability fallback flag is inconsistent")


class WorkersFetchAdapter:
    """Callable compatibility adapter with last-call transport diagnostics only."""

    def __init__(self, context: str, fetch: Any) -> None:
        normalized = str(context or "").strip()
        if not normalized:
            raise ValueError("runtime fetch context is required")
        if len(normalized) > MAX_CONTEXT_LENGTH:
            raise ValueError("runtime fetch context is too long")
        self.context = normalized
        self._fetch = fetch
        self.last_capability_receipt: RuntimeCapabilityReceipt | None = None

    async def __call__(self, url: str, options: dict[str, Any] | None = None, **request_options: Any) -> Any:
        if request_options:
            merged_options = dict(options or {})
            merged_options.update(request_options)
            options = merged_options

        if not options:
            self.last_capability_receipt = RuntimeCapabilityReceipt(
                schema="workers-runtime-capability/v1",
                context=self.context,
                transport=FetchTransport.WORKERS_SDK,
                options_present=False,
                fallback_used=False,
            )
            return await self._fetch(url)

        try:
            from js import Object, fetch as js_fetch
            from pyodide.ffi import to_js
        except ImportError:
            self.last_capability_receipt = RuntimeCapabilityReceipt(
                schema="workers-runtime-capability/v1",
                context=self.context,
                transport=FetchTransport.WORKERS_SDK_FALLBACK,
                options_present=True,
                fallback_used=True,
            )
            return await self._fetch(url, **dict(options))

        js_options = to_js(dict(options), dict_converter=Object.fromEntries)
        self.last_capability_receipt = RuntimeCapabilityReceipt(
            schema="workers-runtime-capability/v1",
            context=self.context,
            transport=FetchTransport.JS_FETCH_FFI,
            options_present=True,
            fallback_used=False,
        )
        return await js_fetch(url, js_options)


def workers_fetch(context: str) -> WorkersFetchAdapter:
    """Return a bounded Worker fetch adapter with request options preserved."""
    try:
        from workers import fetch
    except ImportError as exc:
        raise RuntimeError(f"Cloudflare Workers runtime is required for {context}") from exc
    return WorkersFetchAdapter(context, fetch)
