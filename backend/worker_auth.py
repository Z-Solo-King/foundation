"""Public Worker request/authentication helpers."""
from __future__ import annotations

import hmac
import re
from typing import Any

_URL_RE = re.compile(r"https?://[^\s<>\"']+")
MAX_PUBLIC_JSON_BODY_BYTES = 1_048_576


def extract_source_urls(question: str, explicit=()):
    """Return a bounded, deterministic URL set for source inspection."""
    candidates = list(explicit or ()) + _URL_RE.findall(question or "")
    result = []
    seen = set()
    for raw in candidates:
        url = raw.rstrip(".,);]}")
        if url and url not in seen:
            seen.add(url)
            result.append(url)
    return tuple(result)


def bearer_token(request: Any):
    headers = getattr(request, "headers", {})
    value = headers.get("Authorization")
    if not value or not value.startswith("Bearer "):
        return None
    return value[7:].strip()


def authorized(request: Any, env: Any) -> bool:
    """Authorize public requests; development bypass is explicit and local-only."""
    expected = getattr(env, "AUTH_TOKEN", None)
    environment = str(getattr(env, "ENVIRONMENT", "production") or "production").strip().lower()
    bypass = str(getattr(env, "LOCAL_DEVELOPMENT_AUTH_BYPASS", "") or "").strip().lower() == "true"
    if environment == "development" and bypass:
        return True
    provided = bearer_token(request)
    return bool(expected and provided and hmac.compare_digest(provided, expected))


async def json_object(request: Any):
    """Parse bounded JSON and reject alternate representations at HTTP boundaries."""
    headers = getattr(request, "headers", {})
    content_type = headers.get("Content-Type") or headers.get("content-type")
    if not content_type:
        return None
    media_type = content_type.split(";", 1)[0].strip().lower()
    if media_type != "application/json":
        return None
    content_length = headers.get("Content-Length") or headers.get("content-length")
    if content_length is not None:
        try:
            declared_bytes = int(str(content_length).strip())
        except (TypeError, ValueError):
            return None
        if declared_bytes < 0 or declared_bytes > MAX_PUBLIC_JSON_BODY_BYTES:
            return None
    try:
        value = await request.json()
        return value if isinstance(value, dict) else None
    except Exception:
        return None
