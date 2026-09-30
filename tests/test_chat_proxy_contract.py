import asyncio
import json
from types import SimpleNamespace


def test_chat_proxy_fails_closed_without_operations_binding():
    import worker
    class Request: headers = {}
    payload, status = asyncio.run(worker._operations_chat(SimpleNamespace(), {"message": "x"}, Request()))
    assert status == 503
    assert payload["error"] == "chat_backend_unavailable"


def test_chat_proxy_forwards_auth_and_idempotency():
    import worker
    class Response:
        status = 200
        async def json(self): return {"ok": True, "response": {"text": "hello"}}
    class Binding:
        def __init__(self): self.calls = []
        async def fetch(self, request): self.calls.append(request); return Response()
    class Request: headers = {"Authorization": "Bearer user", "Idempotency-Key": "req-1"}
    binding = Binding()
    payload, status = asyncio.run(worker._operations_chat(SimpleNamespace(OPERATIONS=binding), {"message": "hello"}, Request()))
    assert status == 200
    assert payload["ok"] is True
    request = binding.calls[0]
    assert request.url == "https://chat/v1/chat"
    assert request.method == "POST"
    assert request.headers.get("Authorization") == "Bearer user"
    assert request.headers.get("Idempotency-Key") == "req-1"


def test_chat_stream_proxy_fails_closed_without_operations_binding():
    import worker
    class Request: headers = {}
    payload, status = asyncio.run(worker._operations_chat_stream(SimpleNamespace(), {"message": "x"}, Request()))
    assert status == 503
    assert payload["error"] == "chat_backend_unavailable"


def test_chat_stream_proxy_uses_proven_json_chat():
    import worker
    class Response:
        status = 200
        async def json(self):
            return {"ok": True, "response": {"response_id": "chat-r2", "result_state": "PARTIAL", "text": "hello"}}
    class Binding:
        async def fetch(self, request):
            assert request.url == "https://chat/v1/chat"
            assert request.method == "POST"
            assert request.headers.get("Idempotency-Key") == "req-2"
            return Response()
    class Request: headers = {"Authorization": "Bearer user", "Idempotency-Key": "req-2"}
    body, status = asyncio.run(worker._operations_chat_stream(SimpleNamespace(OPERATIONS=Binding()), {"message": "hello"}, Request()))
    assert body["response"]["text"] == "hello"
    assert status == 200


def test_chat_stream_proxy_handles_binding_error():
    import worker
def test_chat_proxy_translates_authenticated_research_proof_to_private_payload():
    import worker

    class Response:
        status = 200
        async def json(self):
            return {"ok": True, "response": {"text": "structured"}}

    class Binding:
        async def fetch(self, request):
            payload = json.loads(request.body)
            assert payload["operation"] == "knowledge"
            assert payload["research_agent"] is True
            return Response()

    class Request:
        headers = {"Authorization": "Bearer user", "Idempotency-Key": "research-req", "X-Heroic-Research-Proof": "1"}

    original = worker._authorized
    worker._authorized = lambda request, env: True
    try:
        payload, status = asyncio.run(worker._operations_chat(
            SimpleNamespace(OPERATIONS=Binding()),
            {"message": "hello", "operation": "knowledge", "mode": "chat", "strict_zero_cost_only": True},
            Request(),
        ))
    finally:
        worker._authorized = original
    assert status == 200
    assert payload["ok"] is True


def test_chat_proxy_does_not_promote_research_without_proof_header():
    import worker

    class Response:
        status = 200
        async def json(self):
            return {"ok": True, "response": {"text": "normal"}}

    class Binding:
        async def fetch(self, request):
            payload = json.loads(request.body)
            assert "research_agent" not in payload
            return Response()

    class Request:
        headers = {"Authorization": "Bearer user", "Idempotency-Key": "normal-req"}

    original = worker._authorized
    worker._authorized = lambda request, env: True
    try:
        payload, status = asyncio.run(worker._operations_chat(
            SimpleNamespace(OPERATIONS=Binding()),
            {"message": "hello", "operation": "knowledge", "mode": "chat", "strict_zero_cost_only": True},
            Request(),
        ))
    finally:
        worker._authorized = original
    assert status == 200
    assert payload["ok"] is True
