"""Public Worker request/authentication helpers."""
from __future__ import annotations

import hmac
import re
from typing import Any

_URL_RE = re.compile(r"https?://[^\s<>\"']+")


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
    value = request.headers.get("Authorization")
    if not value or not value.startswith("Bearer "):
        return None
    return value[7:].strip()


def authorized(request: Any, env: Any) -> bool:
    """Authorize public requests with an explicit, non-production local bypass only."""
    expected = getattr(env, "AUTH_TOKEN", None)
    environment = str(getattr(env, "ENVIRONMENT", "production") or "production").strip().lower()
    local_bypass = str(getattr(env, "LOCAL_DEVELOPMENT_AUTH_BYPASS", "") or "").strip().lower() == "true"
    if environment == "development" and local_bypass:
        return True
    provided = bearer_token(request)
    return bool(expected and provided and hmac.compare_digest(provided, expected))


async def json_object(request: Any):
    """Parse a JSON object only from an explicit JSON request representation."""
    content_type = request.headers.get("Content-Type") or request.headers.get("content-type")
    if not content_type:
        return None
    media_type = content_type.split(";", 1)[0].strip().lower()
    if media_type != "application/json":
        return None
    try:
        value = await request.json()
        return value if isinstance(value, dict) else None
    except Exception:
        return None
