import pytest

from backend.worker_auth import MAX_PUBLIC_JSON_BODY_BYTES, json_object


class FakeRequest:
    def __init__(self, headers, payload=None):
        self.headers = headers
        self.payload = payload
        self.json_called = False

    async def json(self):
        self.json_called = True
        return self.payload


@pytest.mark.asyncio
async def test_json_object_rejects_oversized_declared_body_before_decode():
    request = FakeRequest(
        {"Content-Type": "application/json", "Content-Length": str(MAX_PUBLIC_JSON_BODY_BYTES + 1)},
        {"ok": True},
    )
    assert await json_object(request) is None
    assert request.json_called is False


@pytest.mark.asyncio
async def test_json_object_rejects_invalid_content_length_before_decode():
    request = FakeRequest(
        {"Content-Type": "application/json", "Content-Length": "not-a-number"},
        {"ok": True},
    )
    assert await json_object(request) is None
    assert request.json_called is False


@pytest.mark.asyncio
async def test_json_object_accepts_bounded_json_body():
    request = FakeRequest(
        {"Content-Type": "application/json", "Content-Length": "12"},
        {"ok": True},
    )
    assert await json_object(request) == {"ok": True}
    assert request.json_called is True
