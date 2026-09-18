from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time


class PublicReadCursorError(ValueError):
    pass


def _payload_bytes(payload: dict[str, object]) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")


def encode_cursor(
    *,
    secret: str,
    subject_fingerprint: str,
    run_id: str,
    snapshot_id: str,
    offset: int,
    expires_at: int,
) -> str:
    if not secret or not subject_fingerprint or not run_id or not snapshot_id:
        raise PublicReadCursorError("cursor scope is incomplete")
    if offset < 0:
        raise PublicReadCursorError("cursor offset must be non-negative")
    now = int(time.time())
    if expires_at <= now:
        raise PublicReadCursorError("cursor expiry must be in the future")
    payload = {
        "v": 1,
        "sub": subject_fingerprint,
        "run": run_id,
        "snap": snapshot_id,
        "off": offset,
        "exp": expires_at,
    }
    body = base64.urlsafe_b64encode(_payload_bytes(payload)).decode("ascii").rstrip("=")
    sig = hmac.new(secret.encode("utf-8"), body.encode("ascii"), hashlib.sha256).hexdigest()
    return f"{body}.{sig}"


def decode_cursor(
    cursor: str,
    *,
    secret: str,
    subject_fingerprint: str,
    run_id: str,
    snapshot_id: str,
    now: int | None = None,
) -> int:
    if not cursor or not secret:
        raise PublicReadCursorError("cursor is missing")
    try:
        body, supplied_sig = cursor.split(".", 1)
        padded = body + "=" * (-len(body) % 4)
        payload = json.loads(base64.urlsafe_b64decode(padded.encode("ascii")))
    except (ValueError, UnicodeError, json.JSONDecodeError, base64.binascii.Error) as exc:
        raise PublicReadCursorError("cursor encoding is invalid") from exc
    expected = hmac.new(secret.encode("utf-8"), body.encode("ascii"), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(supplied_sig, expected):
        raise PublicReadCursorError("cursor signature is invalid")
    if payload.get("v") != 1 or payload.get("sub") != subject_fingerprint or payload.get("run") != run_id:
        raise PublicReadCursorError("cursor scope is invalid")
    if payload.get("snap") != snapshot_id:
        raise PublicReadCursorError("cursor snapshot is stale")
    expiry = payload.get("exp")
    offset = payload.get("off")
    current = int(time.time()) if now is None else now
    if not isinstance(expiry, int) or expiry <= current:
        raise PublicReadCursorError("cursor expired")
    if not isinstance(offset, int) or offset < 0:
        raise PublicReadCursorError("cursor offset is invalid")
    return offset


DEFAULT_PUBLIC_READ_PAGE_SIZE = 50
MAX_PUBLIC_READ_PAGE_SIZE = 50
PUBLIC_READ_CURSOR_TTL_SECONDS = 300
