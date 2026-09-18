"""Public SSE framing at the Foundation edge.

Operations owns chat execution and returns a normal JSON chat envelope through the
service binding. Foundation owns the browser-facing SSE transport so the private
Worker does not have to carry a JavaScript ReadableStream across the service-binding
boundary.
"""
from __future__ import annotations

import asyncio
import json
from collections.abc import Iterable
from time import monotonic

MAX_EVENT_BYTES = 64 * 1024
MAX_EVENTS = 256
MAX_STREAM_OUTPUT_BYTES = MAX_EVENT_BYTES * MAX_EVENTS
MAX_STREAM_DURATION_SECONDS = 60.0
_PROXY_KEEPALIVE: dict[int, tuple[object, object, object]] = {}


def sse_event(event: str, payload: object) -> str:
    body = json.dumps(payload, separators=(",", ":"), ensure_ascii=False)
    return f"event: {event}\ndata: {body}\n\n"


def text_chunks(text: str, *, chunk_size: int = 256) -> tuple[str, ...]:
    if chunk_size < 1:
        raise ValueError("chunk_size must be positive")
    value = str(text)
    return tuple(value[i : i + chunk_size] for i in range(0, len(value), chunk_size))


def buffered_sse_events(
    text: str,
    *,
    response_id: str,
    result_state: str = "COMPLETE",
    usage: dict[str, object] | None = None,
    chunk_size: int = 256,
) -> Iterable[str]:
    """Frame one completed private-chat JSON result as bounded public SSE events."""
    state = str(result_state).upper()
    if state not in {"COMPLETE", "PARTIAL"}:
        state = "FAILED"

    yield sse_event(
        "start",
        {"response_id": response_id, "status": "streaming", "generation": "buffered"},
    )

    for chunk in text_chunks(text, chunk_size=chunk_size):
        yield sse_event("delta", {"text": chunk})

    if usage is not None:
        yield sse_event(
            "usage",
            {
                "input_tokens": usage.get("input_tokens"),
                "output_tokens": usage.get("output_tokens"),
            },
        )

    yield sse_event(
        "done",
        {
            "response_id": response_id,
            "status": "completed" if state == "COMPLETE" else "partial",
            "result_state": state,
        },
    )


def readable_sse_stream(
    events: Iterable[str],
    *,
    max_output_bytes: int = MAX_STREAM_OUTPUT_BYTES,
    max_duration_seconds: float = MAX_STREAM_DURATION_SECONDS,
):
    """Create a lazy, bounded Cloudflare ReadableStream for the public edge."""
    if isinstance(max_output_bytes, bool) or not isinstance(max_output_bytes, int):
        raise ValueError("max_output_bytes must be an integer")
    if max_output_bytes < 1 or max_output_bytes > MAX_STREAM_OUTPUT_BYTES:
        raise ValueError("max_output_bytes is outside the transport safety limit")
    if not isinstance(max_duration_seconds, (int, float)) or isinstance(max_duration_seconds, bool):
        raise ValueError("max_duration_seconds must be numeric")
    if max_duration_seconds <= 0 or max_duration_seconds > MAX_STREAM_DURATION_SECONDS:
        raise ValueError("max_duration_seconds is outside the transport safety limit")

    from js import ReadableStream, TextEncoder
    from pyodide.ffi import create_proxy, to_js

    encoder = TextEncoder.new()
    iterator = iter(events)
    cancelled = False
    stream_key = id(iterator)

    async def start(controller):
        nonlocal cancelled
        started_at = monotonic()
        emitted_bytes = 0
        try:
            for event in iterator:
                if cancelled:
                    return
                encoded = encoder.encode(event)
                emitted_bytes += len(encoded)
                if emitted_bytes > max_output_bytes:
                    controller.error(RuntimeError("stream_output_limit_exceeded"))
                    return
                if monotonic() - started_at >= max_duration_seconds:
                    controller.error(RuntimeError("stream_duration_limit_exceeded"))
                    return
                controller.enqueue(encoded)
                await asyncio.sleep(0)
            if monotonic() - started_at >= max_duration_seconds:
                controller.error(RuntimeError("stream_duration_limit_exceeded"))
                return
            controller.close()
        except BaseException as exc:
            if not cancelled:
                controller.error(exc)
        finally:
            _PROXY_KEEPALIVE.pop(stream_key, None)

    def cancel(_reason):
        nonlocal cancelled
        cancelled = True
        close = getattr(iterator, "close", None)
        if close is not None:
            close()
        _PROXY_KEEPALIVE.pop(stream_key, None)

    start_proxy = create_proxy(start)
    cancel_proxy = create_proxy(cancel)
    _PROXY_KEEPALIVE[stream_key] = (iterator, start_proxy, cancel_proxy)

    try:
        return ReadableStream.new(
            to_js({"start": start_proxy, "cancel": cancel_proxy})
        )
    except BaseException:
        _PROXY_KEEPALIVE.pop(stream_key, None)
        raise
