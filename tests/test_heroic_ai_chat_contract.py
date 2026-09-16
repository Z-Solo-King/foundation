import asyncio
from types import SimpleNamespace


def test_chat_request_rejects_invalid_modes_and_paid_execution():
    from backend.api.models import ChatRequest

    valid = ChatRequest("chat", "request", "hello")
    valid.validate()
    for request in (
        ChatRequest("", "request", "hello"),
        ChatRequest("chat", "", "hello"),
        ChatRequest("chat", "request", ""),
        ChatRequest("chat", "request", "hello", mode="research"),
        ChatRequest("chat", "request", "hello", strict_zero_cost_only=False),
    ):
        try:
            request.validate()
        except ValueError:
            pass
        else:
            raise AssertionError("invalid chat request was accepted")


def test_public_chat_boundary_fails_closed_without_private_binding():
    import worker

    class Request:
        headers = {}

    payload = {"chat_id": "chat", "request_id": "request", "message": "hello", "mode": "chat", "strict_zero_cost_only": True}
    body, status = asyncio.run(worker._operations_chat(SimpleNamespace(), payload, Request()))
    assert status == 503
    assert body["error"] == "chat_backend_unavailable"


def test_public_chat_boundary_uses_internal_service_binding_and_idempotency():
    import worker

    class Response:
        status = 200

        async def json(self):
            return {"ok": True, "response": {"text": "grounded", "status": "completed"}}

    class Binding:
        def __init__(self): self.calls = []

        async def fetch(self, url, options):
            self.calls.append((url, options))
            return Response()

    class Request:
        headers = {"Authorization": "Bearer token", "Idempotency-Key": "request"}

    binding = Binding()
    payload = {"chat_id": "chat", "request_id": "request", "message": "hello", "mode": "chat", "strict_zero_cost_only": True}
    body, status = asyncio.run(worker._operations_chat(SimpleNamespace(OPERATIONS=binding), payload, Request()))
    assert status == 200 and body["ok"] is True
    url, options = binding.calls[0]
    assert url == "https://chat/v1/chat"
    assert options["headers"]["Authorization"] == "Bearer token"
    assert options["headers"]["Idempotency-Key"] == "request"
