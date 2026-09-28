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
import subprocess
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


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
        payload_json = json.dumps(upstream_payload, ensure_ascii=False)
        # Use curl for the outbound edge call. The live preflight uses curl and succeeds;
        # this keeps transport behavior aligned without weakening any Cloudflare policy.
        command = [
            "curl",
            "-sS",
            "--max-time",
            "90",
            "-o",
            "-",
            "-w",
            "\\n%{http_code}",
            "-H",
            "Authorization: Bearer " + self.server.auth_token,
            "-H",
            "Content-Type: application/json",
            "-H",
            "Idempotency-Key: " + request_id,
            "-H",
            "User-Agent: HeroicAI-NightlyResearch/1.0",
            "--data-binary",
            payload_json,
            url,
        ]
        try:
            completed = subprocess.run(command, check=False, capture_output=True, text=True, timeout=95)
        except subprocess.TimeoutExpired:
            self._json({"error": {"message": "upstream_worker_failure", "type": "timeout"}, "request_id": request_digest}, 502)
            return
        except OSError:
            self._json({"error": {"message": "upstream_worker_failure", "type": "curl_unavailable"}, "request_id": request_digest}, 502)
            return

        output_lines = completed.stdout.splitlines()
        try:
            status = int(output_lines[-1]) if output_lines else 0
        except ValueError:
            status = 0
        response_text = "\\n".join(output_lines[:-1]) if output_lines else ""
        try:
            body = json.loads(response_text) if response_text else {}
        except json.JSONDecodeError:
            body = {}

        if completed.returncode != 0:
            self._json({"error": {"message": "upstream_worker_failure", "type": "curl_transport", "status": status}, "request_id": request_digest}, 502)
            return

        if status < 200 or status >= 300:
            details = {"upstream_status": status}
            if isinstance(body, dict):
                error = body.get("error")
                if isinstance(error, dict):
                    message = error.get("message")
                    if isinstance(message, str) and message.strip():
                        details["upstream_error"] = message.strip()[:200]
                    upstream_status = error.get("upstream_status")
                    if isinstance(upstream_status, int):
                        details["upstream_status"] = upstream_status
                elif isinstance(error, str) and error.strip():
                    details["upstream_error"] = error.strip()[:200]
            self._json({"error": {"message": "upstream_worker_rejected", "type": "upstream_http_error", **details}, "request_id": request_digest}, 502)
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
