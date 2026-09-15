import pytest

from backend.api.models import ChatRequest
from worker import _operations_chat


class FakeHeaders:
    def __init__(self, values=None):
        self._values = values or {}

    def get(self, key, default=None):
        return self._values.get(key, default)


class FakeRequest:
    headers = FakeHeaders({"Idempotency-Key": "req-1"})


class FakeUpstreamResponse:
    status = 200

    async def json(self):
        return {"ok": True, "response": {"response_id": "resp-1", "text": "Hello from Heroic AI."}}


class FakeOperations:
    async def fetch(self, url, init):
        assert url == "https://operations/v1/chat"
        assert init["method"] == "POST"
        assert init["headers"]["Content-Type"] == "application/json"
        assert init["headers"]["Idempotency-Key"] == "req-1"
        return FakeUpstreamResponse()


class FakeMissingOperations:
    pass


class FakeEnv:
    OPERATIONS = FakeOperations()


class FakeMissingEnv:
    pass


@pytest.mark.asyncio
async def test_chat_boundary_uses_private_service_binding_and_preserves_response():
    body, status = await _operations_chat(
        FakeEnv(),
        {"chat_id": "chat-1", "request_id": "req-1", "message": "Hello", "mode": "chat", "strict_zero_cost_only": True},
        FakeRequest(),
    )
    assert status == 200
    assert body["response"]["text"] == "Hello from Heroic AI."


@pytest.mark.asyncio
async def test_chat_boundary_fails_closed_without_private_binding():
    body, status = await _operations_chat(
        FakeMissingEnv(),
        {"chat_id": "chat-1", "request_id": "req-1", "message": "Hello", "mode": "chat", "strict_zero_cost_only": True},
        FakeRequest(),
    )
    assert status == 503
    assert body["error"] == "chat_backend_unavailable"


def test_chat_request_rejects_non_chat_mode_and_paid_mode():
    with pytest.raises(ValueError, match="mode=chat"):
        ChatRequest("c", "r", "hello", mode="research").validate()
    with pytest.raises(ValueError, match="strict \$0"):
        ChatRequest("c", "r", "hello", strict_zero_cost_only=False).validate()
