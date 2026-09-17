"""Public Worker request/authentication helpers."""
from __future__ import annotations

import hashlib
import hmac
import re
from typing import Any

from backend.json_admission import validate_json_shape

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
    value = request.headers.get("Authorization")
    if not value or not value.startswith("Bearer "):
        return None
    return value[7:].strip()


def authenticated_subject_fingerprint(request: Any):
    """Derive a non-secret principal fingerprint from the already-authenticated bearer token."""
    token = bearer_token(request)
    if not token:
        return None
    return hashlib.sha256(token.encode()).hexdigest()


def authorized(request: Any, env: Any) -> bool:
    expected = getattr(env, "AUTH_TOKEN", None)
    environment = getattr(env, "ENVIRONMENT", "development")
    if environment != "production" and not expected:
        return True
    provided = bearer_token(request)
    return bool(expected and provided and hmac.compare_digest(provided, expected))


async def json_object(request: Any):
    try:
        value = await request.json()
        if not isinstance(value, dict):
            return None
        validate_json_shape(value)
        return value
    except (TypeError, ValueError):
        return None
    except Exception:
        return None
