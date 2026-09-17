"""Public Worker request/authentication helpers."""
from __future__ import annotations

import hmac
import re
from typing import Any, Optional

_URL_RE = re.compile(r"https?://[^\s<>\"']+")

# Separately-named opt-in flag for the local-development auth bypass.
# Environment name alone is never sufficient to authorize it (see auth_mode).
_BYPASS_ENV_VAR = "LOCAL_DEV_AUTH_BYPASS"
_TRUTHY = {"1", "true", "yes", "on"}


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


def _is_explicit_development(env: Any) -> bool:
    """True only for an exact, explicit "development" environment name.

    Fail closed: anything else (missing, blank, "staging", a typo, "Production")
    is treated as production for authentication purposes.
    """
    environment = getattr(env, "ENVIRONMENT", None)
    if not isinstance(environment, str):
        return False
    return environment.strip().lower() == "development"


def _bypass_flag_set(env: Any) -> bool:
    raw = getattr(env, _BYPASS_ENV_VAR, None)
    if raw is None:
        return False
    return str(raw).strip().lower() in _TRUTHY


def auth_mode(env: Any) -> str:
    """Return the effective authentication mode for this deployment.

    - "required": AUTH_TOKEN is configured; bearer auth is enforced regardless
      of environment.
    - "local_development_bypass": no token configured, ENVIRONMENT is
      explicitly "development", AND the separately-named LOCAL_DEV_AUTH_BYPASS
      flag is explicitly truthy. Environment name alone never grants this.
    - "misconfigured": no token configured and no valid bypass is active.
      Still treated as auth-required by `authorized()` (never anonymous) --
      this mode exists so readiness checks can fail closed instead of the
      Worker silently running as an unauthenticated public API.
    """
    if getattr(env, "AUTH_TOKEN", None):
        return "required"
    if _is_explicit_development(env) and _bypass_flag_set(env):
        return "local_development_bypass"
    return "misconfigured"


def authorized(request: Any, env: Any) -> bool:
    if auth_mode(env) == "local_development_bypass":
        return True
    expected = getattr(env, "AUTH_TOKEN", None)
    provided = bearer_token(request)
    return bool(expected and provided and hmac.compare_digest(provided, expected))


def auth_readiness_error(env: Any) -> Optional[str]:
    """Return a readiness-blocking error string, or None if auth config is sound.

    Missing production authentication configuration is a hard readiness
    failure, never an implicit anonymous mode.
    """
    mode = auth_mode(env)
    if mode == "misconfigured":
        return "AUTH_TOKEN is not configured and no local-development auth bypass is active"
    if mode == "local_development_bypass" and not _is_explicit_development(env):
        # Defense in depth: unreachable via auth_mode's own check today, but
        # readiness must never pass if this combination is ever produced.
        return "local-development auth bypass is active outside an explicit development environment"
    return None


async def json_object(request: Any):
    try:
        value = await request.json()
        return value if isinstance(value, dict) else None
    except Exception:
        return None
