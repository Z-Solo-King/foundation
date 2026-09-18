import time

import pytest

from backend.public_read_cursor import (
    PublicReadCursorError,
    decode_cursor,
    encode_cursor,
)


SECRET = "subject-secret"
SUBJECT = "subject-1"
RUN = "run-1"
SNAPSHOT = "2026-09-18T03:00:00+00:00"


def valid_cursor(offset=0):
    return encode_cursor(
        secret=SECRET,
        subject_fingerprint=SUBJECT,
        run_id=RUN,
        snapshot_id=SNAPSHOT,
        offset=offset,
        expires_at=int(time.time()) + 300,
    )


def test_cursor_round_trip_is_deterministic_and_scoped():
    cursor = valid_cursor(25)
    assert decode_cursor(
        cursor,
        secret=SECRET,
        subject_fingerprint=SUBJECT,
        run_id=RUN,
        snapshot_id=SNAPSHOT,
        now=int(time.time()),
    ) == 25


def test_cursor_rejects_missing_scope_and_bad_inputs():
    with pytest.raises(PublicReadCursorError):
        encode_cursor(secret="", subject_fingerprint=SUBJECT, run_id=RUN, snapshot_id=SNAPSHOT, offset=0, expires_at=int(time.time()) + 10)
    with pytest.raises(PublicReadCursorError):
        encode_cursor(secret=SECRET, subject_fingerprint=SUBJECT, run_id=RUN, snapshot_id=SNAPSHOT, offset=-1, expires_at=int(time.time()) + 10)
    with pytest.raises(PublicReadCursorError):
        encode_cursor(secret=SECRET, subject_fingerprint=SUBJECT, run_id=RUN, snapshot_id=SNAPSHOT, offset=0, expires_at=int(time.time()) - 1)
    with pytest.raises(PublicReadCursorError):
        decode_cursor("", secret=SECRET, subject_fingerprint=SUBJECT, run_id=RUN, snapshot_id=SNAPSHOT)


def test_cursor_rejects_malformed_signature_scope_snapshot_and_expiry():
    cursor = valid_cursor()
    bad_body = cursor[:-1] + ("0" if cursor[-1] != "0" else "1")
    with pytest.raises(PublicReadCursorError, match="signature"):
        decode_cursor(bad_body, secret=SECRET, subject_fingerprint=SUBJECT, run_id=RUN, snapshot_id=SNAPSHOT)

    with pytest.raises(PublicReadCursorError, match="scope"):
        decode_cursor(cursor, secret=SECRET, subject_fingerprint="other", run_id=RUN, snapshot_id=SNAPSHOT)

    with pytest.raises(PublicReadCursorError, match="snapshot"):
        decode_cursor(cursor, secret=SECRET, subject_fingerprint=SUBJECT, run_id=RUN, snapshot_id="changed")

    expired = encode_cursor(
        secret=SECRET,
        subject_fingerprint=SUBJECT,
        run_id=RUN,
        snapshot_id=SNAPSHOT,
        offset=0,
        expires_at=int(time.time()) + 1,
    )
    with pytest.raises(PublicReadCursorError, match="expired"):
        decode_cursor(expired, secret=SECRET, subject_fingerprint=SUBJECT, run_id=RUN, snapshot_id=SNAPSHOT, now=int(time.time()) + 2)


def test_cursor_rejects_bad_encoding_and_invalid_payload_types():
    with pytest.raises(PublicReadCursorError, match="encoding"):
        decode_cursor("not-valid", secret=SECRET, subject_fingerprint=SUBJECT, run_id=RUN, snapshot_id=SNAPSHOT)

    import base64
    import hashlib
    import hmac
    import json

    payload = {"v": 1, "sub": SUBJECT, "run": RUN, "snap": SNAPSHOT, "off": "zero", "exp": int(time.time()) + 300}
    body = base64.urlsafe_b64encode(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).decode().rstrip("=")
    sig = hmac.new(SECRET.encode(), body.encode(), hashlib.sha256).hexdigest()
    with pytest.raises(PublicReadCursorError, match="offset"):
        decode_cursor(f"{body}.{sig}", secret=SECRET, subject_fingerprint=SUBJECT, run_id=RUN, snapshot_id=SNAPSHOT)
