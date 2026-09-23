import asyncio
from types import SimpleNamespace


def test_chat_request_rejects_invalid_modes_paid_execution_and_bounds():
    from backend.api.models import ChatRequest
    valid = ChatRequest("chat", "request", "hello"); valid.validate()
    invalid = (ChatRequest("", "request", "hello"), ChatRequest("chat", "", "hello"), ChatRequest("chat", "request", ""), ChatRequest("chat", "request", "x" * 16_385), ChatRequest("chat", "request", "hello", mode="research"), ChatRequest("chat", "request", "hello", strict_zero_cost_only=False), ChatRequest("chat", "request", "hello", metadata={str(i): "v" for i in range(33)}))
    for request in invalid:
        try: request.validate()
        except ValueError: pass
        else: raise AssertionError("invalid chat request was accepted")


def test_public_chat_boundary_fails_closed_without_private_binding():
    import worker
    class Request: headers = {}
    payload = {"chat_id": "chat", "request_id": "request", "message": "hello", "mode": "chat", "strict_zero_cost_only": True}
    body, status = asyncio.run(worker._operations_chat(SimpleNamespace(), payload, Request()))
    assert status == 503 and body["error"] == "chat_backend_unavailable"


def test_public_chat_boundary_uses_internal_service_binding_and_idempotency():
    import json, worker
    class Response:
        status = 200
        async def json(self): return {"ok": True, "response": {"text": "grounded", "status": "completed"}}
    class Binding:
        def __init__(self): self.calls = []
        async def fetch(self, request): self.calls.append(request); return Response()
    class Request: headers = {"Authorization": "Bearer token", "Idempotency-Key": "request"}
    binding = Binding(); payload = {"chat_id": "chat", "request_id": "request", "message": "hello", "mode": "chat", "strict_zero_cost_only": True}
    body, status = asyncio.run(worker._operations_chat(SimpleNamespace(OPERATIONS=binding), payload, Request()))
    assert status == 200 and body["ok"] is True
    request = binding.calls[0]; assert request.url == "https://chat/v1/chat"
    assert request.method == "POST"
    assert request.headers.get("Authorization") == "Bearer token" and request.headers.get("Idempotency-Key") == "request"


def test_public_chat_boundary_returns_fail_closed_on_invalid_private_response():
    import worker
    class Response:
        status = 200
        async def json(self): return ["not", "an", "object"]
    class Binding:
        async def fetch(self, request): return Response()
    class Request: headers = {}
    payload = {"chat_id": "chat", "request_id": "request", "message": "hello", "mode": "chat", "strict_zero_cost_only": True}
    body, status = asyncio.run(worker._operations_chat(SimpleNamespace(OPERATIONS=Binding()), payload, Request()))
    assert status == 503 and body["error"] == "invalid_private_chat_response"


def test_public_chat_boundary_returns_unavailable_on_binding_error():
    import worker
    class Binding:
        async def fetch(self, request): raise RuntimeError("binding unavailable")
    class Request: headers = {}
    payload = {"chat_id": "chat", "request_id": "request", "message": "hello", "mode": "chat", "strict_zero_cost_only": True}
    body, status = asyncio.run(worker._operations_chat(SimpleNamespace(OPERATIONS=Binding()), payload, Request()))
    assert status == 503 and body["error"] == "chat_backend_unavailable"


def test_public_worker_chat_route_validation_and_fail_closed_paths():
    import worker
    class Request:
        def __init__(self, payload=None, headers=None):
            self.method = "POST"; self.url = "https://example/api/v1/chat"; self._payload = payload; self.headers = headers or {}
        async def json(self): return self._payload
    class Binding:
        async def fetch(self, request):
            class Response:
                status = 200
                async def json(self): return {"ok": True, "response": {"text": "grounded", "status": "completed"}}
            return Response()
    payload = {"chat_id": "chat", "request_id": "request", "message": "hello", "mode": "chat", "strict_zero_cost_only": True}
    unauthorized = worker.Default(); unauthorized.env = SimpleNamespace(AUTH_TOKEN="secret")
    response = asyncio.run(unauthorized.fetch(Request(payload))); assert response.status == 401
    dev = {"ENVIRONMENT": "development", "AUTH_TOKEN": None, "LOCAL_DEVELOPMENT_AUTH_BYPASS": "true"}
    invalid_json = worker.Default(); invalid_json.env = SimpleNamespace(**dev, OPERATIONS=Binding())
    response = asyncio.run(invalid_json.fetch(Request(None, {"Content-Type": "application/json"}))); assert response.status == 400
    malformed = worker.Default(); malformed.env = SimpleNamespace(**dev, OPERATIONS=Binding())
    response = asyncio.run(malformed.fetch(Request({**payload, "mode": "research"}, {"Content-Type": "application/json"}))); assert response.status == 400
    unavailable = worker.Default(); unavailable.env = SimpleNamespace(**dev)
    response = asyncio.run(unavailable.fetch(Request(payload, {"Content-Type": "application/json"}))); assert response.status == 503
    success = worker.Default(); success.env = SimpleNamespace(**dev, OPERATIONS=Binding())
    response = asyncio.run(success.fetch(Request(payload, {"Idempotency-Key": "request", "Content-Type": "application/json"}))); assert response.status == 200



def test_chat_request_accepts_governed_operation_fields_with_bounds():
    from backend.api.models import ChatRequest

    request = ChatRequest(
        "chat",
        "request",
        "https://example.com/",
        operation="map",
        input_records=[{"id": "policy-probe"}],
    )
    request.validate()


def test_chat_request_rejects_unknown_operation_and_oversized_input_records():
    from backend.api.models import ChatRequest, MAX_CHAT_INPUT_RECORDS, MAX_CHAT_RECORD_FIELDS

    invalid_operation = ChatRequest("chat", "request", "hello", operation="execute_anything")
    try:
        invalid_operation.validate()
    except ValueError:
        pass
    else:
        raise AssertionError("unknown chat operation was accepted")

    too_many = ChatRequest(
        "chat",
        "request",
        "hello",
        operation="map",
        input_records=[{"id": str(i)} for i in range(MAX_CHAT_INPUT_RECORDS + 1)],
    )
    try:
        too_many.validate()
    except ValueError:
        pass
    else:
        raise AssertionError("oversized input_records was accepted")

    too_wide = ChatRequest(
        "chat",
        "request",
        "hello",
        operation="map",
        input_records=[{str(i): "x" for i in range(MAX_CHAT_RECORD_FIELDS + 1)}],
    )
    try:
        too_wide.validate()
    except ValueError:
        pass
    else:
        raise AssertionError("oversized input record was accepted")
