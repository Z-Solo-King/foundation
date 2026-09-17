from datetime import datetime, timezone

import pytest

from foundation_core.stage_receipt import StageReceipt, can_resume, validate_chain


def receipt(**overrides):
    values = {
        "request_fingerprint": "req",
        "stage": "research",
        "input_fingerprint": "in",
        "output_fingerprint": "out",
        "method": "deterministic",
        "resource_units": 2,
    }
    values.update(overrides)
    return StageReceipt(**values)


def test_can_resume_rejects_expired_receipt():
    item = receipt(
        created_at="2026-09-16T00:00:00+00:00",
        expires_at="2026-09-17T00:00:00+00:00",
    )
    assert not can_resume(
        item,
        request_fingerprint="req",
        input_fingerprint="in",
        now=datetime(2026, 9, 17, 0, 0, tzinfo=timezone.utc),
    )


def test_can_resume_accepts_unexpired_receipt():
    item = receipt(
        created_at="2026-09-16T00:00:00+00:00",
        expires_at="2026-09-18T00:00:00+00:00",
    )
    assert can_resume(
        item,
        request_fingerprint="req",
        input_fingerprint="in",
        now=datetime(2026, 9, 17, 0, 0, tzinfo=timezone.utc),
    )


def test_receipt_rejects_expiry_before_creation():
    with pytest.raises(ValueError, match="expires_at"):
        receipt(
            created_at="2026-09-18T00:00:00+00:00",
            expires_at="2026-09-17T00:00:00+00:00",
        )


def test_validate_chain_enforces_cumulative_resource_ceiling():
    first = receipt(resource_units=3)
    second = receipt(
        stage="verify",
        input_fingerprint="out",
        output_fingerprint="out2",
        parent_receipt_fingerprint=first.fingerprint(),
        resource_units=4,
    )
    with pytest.raises(ValueError, match="max_resource_units"):
        validate_chain((first, second), max_resource_units=6)


def test_validate_chain_allows_cumulative_resource_within_ceiling():
    first = receipt(resource_units=3)
    second = receipt(
        stage="verify",
        input_fingerprint="out",
        output_fingerprint="out2",
        parent_receipt_fingerprint=first.fingerprint(),
        resource_units=4,
    )
    assert validate_chain((first, second), max_resource_units=7)
