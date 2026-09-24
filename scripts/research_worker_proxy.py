#!/usr/bin/env python3
"""Loopback OpenAI-compatible adapter for nightly research.

The CI runner cannot use the private Operations service binding directly. This adapter
keeps the research executor contract unchanged while routing each model request through
the authenticated production-safe Foundation Worker, which in turn uses the private
Operations service binding and native Cloudflare Workers AI binding.

Only 127.0.0.1 is served. The CI bearer token is deliberately not logged.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.error import HTTPError
from urllib.request import Request, urlopen


MAX_BODY_BYTES = 131_072
MAX_MESSAGE_CHARS = 11_800


def _compact_messages(messages: object) -> str:
    if not isinstance(messages, list) or not messages:
        raise ValueError("messages must be a non-empty list")

    system_parts: list[str] = []
    conversation_parts: list[str] = []
    for item in messages:
        if not isinstance(item, dict):
            continue
        role = str(item.get("role", "")).strip().lower()
        content = item.get("content")
        if not isinstance(content, str) or not content.strip():
            continue
        content = content.strip()
        if role == "system":
            system_parts.append(content)
        else:
            conversation_parts.append(f"{role or 'user'}: {content}")

    if not conversation_parts:
        raise ValueError("messages contain no usable user content")

    sections: list[str] = []
    if system_parts:
        sections.append("Research execution instructions:\n" + "\n\n".join(system_parts))
    sections.append("Research request:\n" + "\n\n".join(conversation_parts))
    message = "\n\n".join(sections).strip()
    if len(message) > MAX_MESSAGE_CHARS:
        message = message[:MAX_MESSAGE_CHARS]
    return message


def _safe_upstream_error_details(error: HTTPError) -> dict[str, object]:
    """Expose only bounded, non-secret fields from an upstream HTTP error."""
    details: dict[str, object] = {"upstream_status": int(error.code)}
    try:
        raw = error.read(MAX_BODY_BYTES)
        body = json.loads(raw.decode("utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return details
    if not isinstance(body, dict):
        return details
    upstream_error = body.get("error")
    if isinstance(upstream_error, str) and upstream_error.strip():
        details["upstream_error"] = upstream_error.strip()[:200]
    response = body.get("response")
    if isinstance(response, dict):
        generation_status = response.get("generation_status")
        provider = response.get("provider")
        if isinstance(generation_status, str) and generation_status.strip():
            details["upstream_generation_status"] = generation_status.strip()[:80]
        if isinstance(provider, str) and provider.strip():
            details["upstream_provider"] = provider.strip()[:120]
    return details


class Handler(BaseHTTPRequestHandler):
    server_version = "ResearchWorkerProxy/1.0"

    def _json(self, payload: dict[str, object], status: int = 200) -> None:
        encoded = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(encoded)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(encoded)

    def log_message(self, fmt: str, *args: object) -> None:
        # Never emit request headers or bodies; secrets must not enter CI logs.
        return

    def do_GET(self) -> None:
        if self.path == "/health":
            self._json({"ok": True, "service": "research-worker-proxy"})
            return
        self._json({"ok": False, "error": "not_found"}, 404)

    def do_POST(self) -> None:
        if self.path != "/chat/completions":
            self._json({"ok": False, "error": "not_found"}, 404)
            return

        authorization = self.headers.get("Authorization", "")
        if authorization != "Bearer local-worker-proxy":
            self._json({"ok": False, "error": "unauthorized"}, 401)
            return

        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            self._json({"ok": False, "error": "invalid_content_length"}, 400)
            return
        if length <= 0 or length > MAX_BODY_BYTES:
            self._json({"ok": False, "error": "request_too_large"}, 413)
            return

        try:
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
            model = str(payload.get("model", "")).strip()
            message = _compact_messages(payload.get("messages"))
            if not model:
                raise ValueError("model is required")
        except (UnicodeDecodeError, json.JSONDecodeError, TypeError, ValueError) as exc:
            self._json({"ok": False, "error": "invalid_request", "detail": str(exc)[:200]}, 400)
            return

        request_id = "research-proxy-" + uuid.uuid4().hex
        # Stable, bounded request identity for logs/diagnostics without exposing payloads.
        request_digest = hashlib.sha256(request_id.encode("utf-8")).hexdigest()[:16]
        upstream_payload = {
            "chat_id": request_id,
            "request_id": request_id,
            "message": message,
            "mode": "chat",
            "operation": "knowledge",
            "strict_zero_cost_only": True,
            # Nightly research is evidence-gated: deterministic fallback cannot count as provider execution.
            "require_model_generation": True,
        }

        url = self.server.public_worker_url.rstrip("/") + "/api/v1/chat"
        request = Request(
            url,
            data=json.dumps(upstream_payload, ensure_ascii=False).encode("utf-8"),
            headers={
                "Authorization": "Bearer " + self.server.auth_token,
                "Content-Type": "application/json",
                "Idempotency-Key": request_id,
            },
            method="POST",
        )

        try:
            with urlopen(request, timeout=90) as response:
                body = json.loads(response.read().decode("utf-8"))
                status = int(response.status)
        except HTTPError as exc:
            details = _safe_upstream_error_details(exc)
            self._json(
                {"error": {"message": "upstream_worker_rejected", "type": "upstream_http_error", **details}, "request_id": request_digest},
                502,
            )
            return
        except Exception as exc:
            self._json(
                {"error": {"message": "upstream_worker_failure", "type": type(exc).__name__}, "request_id": request_digest},
                502,
            )
            return

        if status < 200 or status >= 300 or not isinstance(body, dict):
            self._json(
                {"error": {"message": "upstream_worker_rejected", "type": "upstream_error"}, "request_id": request_digest},
                502,
            )
            return

        response = body.get("response")
        if not isinstance(response, dict):
            self._json({"error": {"message": "upstream_response_missing", "type": "protocol_error"}}, 502)
            return

        text = response.get("text")
        if not isinstance(text, str) or not text.strip():
            self._json({"error": {"message": "upstream_model_text_missing", "type": "protocol_error"}}, 502)
            return

        generation_status = response.get("generation_status")
        if generation_status != "model_generated" or not response.get("provider"):
            self._json(
                {
                    "error": {
                        "message": "provider_required_but_unavailable",
                        "type": "provider_execution_not_proven",
                        "generation_status": str(generation_status or "unknown")[:80],
                        "provider": str(response.get("provider") or "")[:120],
                    },
                    "request_id": request_digest,
                },
                502,
            )
            return

        usage = response.get("usage")
        normalized_usage = usage if isinstance(usage, dict) else {}
        self._json(
            {
                "id": "research-" + request_id,
                "object": "chat.completion",
                "model": str(response.get("model") or model),
                "provider": str(response.get("provider") or "cloudflare_workers_ai"),
                "execution_id": request_id,
                "choices": [
                    {
                        "index": 0,
                        "message": {"role": "assistant", "content": text},
                        "finish_reason": "stop",
                    }
                ],
                "usage": normalized_usage,
            }
        )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--public-worker-url", required=True)
    parser.add_argument("--auth-token", default="")
    parser.add_argument("--bind", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()

    auth_token = args.auth_token or os.environ.get("RESEARCH_PROXY_AUTH_TOKEN", "")
    if not auth_token:
        parser.error("research proxy auth token is required")
    server = ThreadingHTTPServer((args.bind, args.port), Handler)
    server.public_worker_url = args.public_worker_url
    server.auth_token = auth_token
    print(json.dumps({"ok": True, "bind": args.bind, "port": args.port, "service": "research-worker-proxy"}), flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
