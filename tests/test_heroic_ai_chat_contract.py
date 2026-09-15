import pytest

from backend.api.models import ChatRequest
from worker import Default, _operations_chat


class FakeHeaders:
    def __init__(self, values=None):
        self._values = values or {}

    def get(self, key, default=None):
        return self._values.get(key, default)


class FakeRequest:
    headers = FakeHeaders({"Idempotency-Key": "req-1"})
    method = "POST"
    url = "https://example.test/api/v1/chat"

    def __init__(self, payload=None, headers=None):
        self._payload = payload
        if headers is not None:
            self.headers = FakeHeaders(headers)

    async def json(self):
        return self._payload


class FakeUpstreamResponse:
    def __init__(self, body=None, status=200):
        self.body = body
        self.status = status

    async def json(self):
        return self.body


class FakeOperations:
    def __init__(self, response=None, error=None):
        self.response = response or FakeUpstreamResponse(
            {"ok": True, "response": {"response_id": "resp-1", "text": "Hello from Heroic AI."}}
        )
        self.error = error

    async def fetch(self, url, init):
        assert url == "https://chat/v1/chat"
        assert init["method"] == "POST"
        assert init["headers"]["Content-Type"] == "application/json"
        if "Idempotency-Key" in init["headers"]:
            assert init["headers"]["Idempotency-Key"] == "req-1"
        if "Authorization" in init["headers"]:
            assert init["headers"]["Authorization"] == "Bearer token"
        return await self._raise_or_return()

    async def _raise_or_return(self):
        if self.error:
            raise self.error
        return self.response


class FakeMissingEnv:
    pass


class FakeEnv:
    def __init__(self, operations=None):
        self.OPERATIONS = operations or FakeOperations()


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
async def test_chat_boundary_forwards_bearer_and_handles_invalid_or_failed_upstream():
    authenticated_request = FakeRequest(headers={"Authorization": "Bearer token", "Idempotency-Key": "req-1"})
    body, status = await _operations_chat(
        FakeEnv(FakeOperations(response=FakeUpstreamResponse("not-an-object"))),
        {"chat_id": "chat-1", "request_id": "req-1", "message": "Hello"},
        authenticated_request,
    )
    assert status == 503
    assert body["error"] == "invalid_private_chat_response"

    body, status = await _operations_chat(
        FakeEnv(FakeOperations(error=RuntimeError("upstream down"))),
        {"chat_id": "chat-1", "request_id": "req-1", "message": "Hello"},
        FakeRequest(),
    )
    assert status == 503
    assert body["error"] == "chat_backend_unavailable"


@pytest.mark.asyncio
async def test_chat_boundary_fails_closed_without_private_binding():
    body, status = await _operations_chat(
        FakeMissingEnv(),
        {"chat_id": "chat-1", "request_id": "req-1", "message": "Hello", "mode": "chat", "strict_zero_cost_only": True},
        FakeRequest(),
    )
    assert status == 503
    assert body["error"] == "chat_backend_unavailable"


@pytest.mark.asyncio
async def test_chat_boundary_allows_missing_optional_headers():
    request = FakeRequest(headers={})
    operations = FakeOperations()
    body, status = await _operations_chat(
        FakeEnv(operations),
        {"chat_id": "chat-1", "request_id": "req-1", "message": "Hello"},
        request,
    )
    assert status == 200
    assert body["ok"] is True


def test_chat_request_validation_rejects_invalid_contracts():
    cases = [
        (ChatRequest("", "r", "hello"), "chat_id"),
        (ChatRequest("c", "", "hello"), "request_id"),
        (ChatRequest("c", "r", ""), "message"),
        (ChatRequest("c", "r", "x" * 16_385), "supported length"),
        (ChatRequest("c", "r", "hello", mode="research"), "mode=chat"),
        (ChatRequest("c", "r", "hello", strict_zero_cost_only=False), r"strict \$0"),
        (ChatRequest("c", "r", "hello", metadata={str(i): "v" for i in range(33)}), "field count"),
    ]
    for request, message in cases:
        with pytest.raises(ValueError, match=message):
            request.validate()


def test_chat_request_accepts_bounded_metadata():
    request = ChatRequest("c", "r", "hello", metadata={"source": "ui", "mode": "chat"})
    assert request.validate() is None


@pytest.mark.asyncio
async def test_public_chat_route_returns_private_response(monkeypatch):
    monkeypatch.setattr("worker._authorized", lambda request, env: True)
    handler = Default()
    handler.env = FakeEnv()
    response = await handler.fetch(
        FakeRequest(
            {
                "chat_id": "chat-1",
                "request_id": "req-1",
                "message": "Hello",
                "mode": "chat",
                "strict_zero_cost_only": True,
            }
        )
    )
    assert response.status == 200


@pytest.mark.asyncio
async def test_public_chat_route_rejects_unauthorized_invalid_json_and_invalid_contract(monkeypatch):
    handler = Default()
    handler.env = FakeEnv()

    monkeypatch.setattr("worker._authorized", lambda request, env: False)
    response = await handler.fetch(FakeRequest({}))
    assert response.status == 401

    monkeypatch.setattr("worker._authorized", lambda request, env: True)
    response = await handler.fetch(FakeRequest(None))
    assert response.status == 400

    response = await handler.fetch(FakeRequest({"chat_id": "c"}))
    assert response.status == 400
