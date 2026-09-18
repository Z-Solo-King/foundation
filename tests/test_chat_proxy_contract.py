import asyncio
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
    class Binding:
        async def fetch(self, request): raise RuntimeError("binding unavailable")
    class Request: headers = {}
    payload, status = asyncio.run(worker._operations_chat_stream(SimpleNamespace(OPERATIONS=Binding()), {"message": "hello"}, Request()))
    assert status == 503
    assert payload["error"] == "chat_backend_unavailable"


def test_chat_sse_body_rejects_invalid_private_response():
    import pytest
    import worker

    with pytest.raises(ValueError, match="invalid_private_chat_response"):
        worker._chat_sse_body({"ok": True})

    with pytest.raises(ValueError, match="stream_execution_identity_missing"):
        worker._chat_sse_body({"response": {"result_state": "PARTIAL", "text": "x"}})

    with pytest.raises(ValueError, match="blocked_chat_stream"):
        worker._chat_sse_body({"response": {"response_id": "r", "result_state": "BLOCKED", "text": "x"}})


def test_chat_sse_body_covers_usage_complete_and_bounded_size():
    import pytest
    import worker

    body = worker._chat_sse_body({
        "response": {
            "response_id": "chat-complete",
            "result_state": "COMPLETE",
            "text": "x" * 300,
            "generation_status": "model_generated",
            "usage": {"input_tokens": 3, "output_tokens": 2},
        }
    })
    assert "event: usage" in body
    assert '"status":"completed"' in body
    assert '"result_state":"COMPLETE"' in body

    with pytest.raises(ValueError, match="stream response exceeds supported size"):
        worker._chat_sse_body({
            "response": {
                "response_id": "too-large",
                "result_state": "PARTIAL",
                "text": "x" * (worker.MAX_PUBLIC_JSON_BODY_BYTES + 1),
            }
        })


def test_chat_sse_body_has_start_delta_and_done_contract():
    import worker
    body = worker._chat_sse_body({
        "ok": True,
        "response": {
            "response_id": "chat-r1",
            "result_state": "PARTIAL",
            "text": "hello world",
            "generation_status": "deterministic_fallback",
        },
    })
    assert "event: start" in body
    assert "event: delta" in body
    assert "hello world" in body
    assert "event: done" in body
    assert '"result_state":"PARTIAL"' in body




def test_public_worker_chat_stream_returns_private_non_200(monkeypatch):
    import worker

    async def backend(*args, **kwargs):
        return {"ok": False, "error": "chat_backend_unavailable"}, 503

    monkeypatch.setattr(worker, "_operations_chat_stream", backend)
    monkeypatch.setattr(worker, "_public_admit", lambda *args, **kwargs: asyncio.sleep(0, result=(type("D", (), {"allowed": True})(), None)))

    class Request:
        method = "POST"
        url = "https://example/api/v1/chat/stream"
        headers = {"Authorization": "Bearer secret", "Idempotency-Key": "r2"}
        async def json(self):
            return {"chat_id": "c2", "request_id": "r2", "message": "hello", "strict_zero_cost_only": True}

    instance = worker.Default()
    instance.env = SimpleNamespace(AUTH_TOKEN="secret", DB=object(), ENVIRONMENT="development", LOCAL_DEVELOPMENT_AUTH_BYPASS="true")
    response = asyncio.run(instance.fetch(Request()))
    assert response.status == 503


def test_public_worker_chat_stream_returns_503_for_invalid_sse_payload(monkeypatch):
    import worker

    async def backend(*args, **kwargs):
        return {"ok": True, "response": {"result_state": "BLOCKED"}}, 200

    monkeypatch.setattr(worker, "_operations_chat_stream", backend)
    monkeypatch.setattr(worker, "_public_admit", lambda *args, **kwargs: asyncio.sleep(0, result=(type("D", (), {"allowed": True})(), None)))

    class Request:
        method = "POST"
        url = "https://example/api/v1/chat/stream"
        headers = {"Authorization": "Bearer secret", "Idempotency-Key": "r3"}
        async def json(self):
            return {"chat_id": "c3", "request_id": "r3", "message": "hello", "strict_zero_cost_only": True}

    instance = worker.Default()
    instance.env = SimpleNamespace(AUTH_TOKEN="secret", DB=object(), ENVIRONMENT="development", LOCAL_DEVELOPMENT_AUTH_BYPASS="true")
    response = asyncio.run(instance.fetch(Request()))
    assert response.status == 503


def test_public_worker_chat_stream_route_requires_auth():
    import worker
    class Request:
        method = "POST"; url = "https://example/api/v1/chat/stream"
        def __init__(self, headers, body): self.headers = headers; self._body = body
        async def json(self): return self._body
    instance = worker.Default(); instance.env = SimpleNamespace(AUTH_TOKEN="secret")
    response = asyncio.run(instance.fetch(Request({}, {"chat_id": "c1", "request_id": "r1", "message": "hello"})))
    assert response.status == 401


def test_public_worker_chat_stream_route_validates_payload():
    import worker
    class Request:
        method = "POST"; url = "https://example/api/v1/chat/stream"
        def __init__(self, headers, body): self.headers = headers; self._body = body
        async def json(self): return self._body
    instance = worker.Default(); instance.env = SimpleNamespace(AUTH_TOKEN="secret")
    response = asyncio.run(instance.fetch(Request({"Authorization": "Bearer secret", "Content-Type": "application/json"}, {"message": "hello"})))
    assert response.status == 400


def test_public_worker_chat_stream_route_returns_invalid_json_for_non_object_body():
    import worker
    class Request:
        method = "POST"; url = "https://example/api/v1/chat/stream"; headers = {"Authorization": "Bearer secret", "Content-Type": "application/json"}
        async def json(self): return "not an object"
    instance = worker.Default(); instance.env = SimpleNamespace(AUTH_TOKEN="secret")
    response = asyncio.run(instance.fetch(Request()))
    assert response.status == 400


def test_public_worker_chat_stream_route_returns_private_unavailable_response_without_binding():
    import worker
    class Request:
        method = "POST"; url = "https://example/api/v1/chat/stream"; headers = {"Authorization": "Bearer secret", "Content-Type": "application/json"}
        async def json(self): return {"chat_id": "c1", "request_id": "r1", "message": "hello", "strict_zero_cost_only": True}
    instance = worker.Default(); instance.env = SimpleNamespace(AUTH_TOKEN="secret")
    response = asyncio.run(instance.fetch(Request()))
    assert response.status == 503


def test_public_worker_chat_stream_route_frames_proven_private_json():
    import worker
    class Response:
        status = 200
        async def json(self):
            return {"ok": True, "response": {"response_id": "chat-r1", "result_state": "PARTIAL", "text": "hello", "generation_status": "deterministic_fallback"}}
    class Binding:
        async def fetch(self, request):
            assert request.url == "https://chat/v1/chat"
            assert request.method == "POST"
            assert request.headers.get("Authorization") == "Bearer secret"
            assert request.headers.get("Idempotency-Key") == "r1"
            return Response()
    class Request:
        method = "POST"; url = "https://example/api/v1/chat/stream"; headers = {"Authorization": "Bearer secret", "Idempotency-Key": "r1", "Content-Type": "application/json"}
        async def json(self): return {"chat_id": "c1", "request_id": "r1", "message": "hello", "strict_zero_cost_only": True}
    instance = worker.Default(); instance.env = SimpleNamespace(AUTH_TOKEN="secret", OPERATIONS=Binding(), ENVIRONMENT="development", LOCAL_DEVELOPMENT_AUTH_BYPASS="true")
    response = asyncio.run(instance.fetch(Request()))
    assert response.status == 200


def test_public_worker_chat_route_requires_auth_and_validates_payload():
    import worker
    class Request:
        method = "POST"; url = "https://example/api/v1/chat"
        def __init__(self, headers, body): self.headers = headers; self._body = body
        async def json(self): return self._body
    unauthorized = worker.Default(); unauthorized.env = SimpleNamespace(AUTH_TOKEN="secret")
    response = asyncio.run(unauthorized.fetch(Request({}, {"message": "hello"})))
    assert response.status == 401
    invalid = worker.Default(); invalid.env = SimpleNamespace(AUTH_TOKEN="secret")
    response = asyncio.run(invalid.fetch(Request({"Authorization": "Bearer secret", "Content-Type": "application/json"}, {"message": "hello"})))
    assert response.status == 400


def test_public_sse_response_uses_only_allowlisted_headers(monkeypatch):
    import worker

    calls = []

    class Response:
        def __init__(self, body, *, status=200, headers=None):
            calls.append((body, status, headers))
            self.status = status

    monkeypatch.setattr(worker, "Response", Response)
    upstream = type("Upstream", (), {"body": b"data: hello\\n\\n", "status": 200})()
    response = worker._public_sse_response(upstream)

    assert response.status == 200
    body, status, headers = calls[0]
    assert body == b"data: hello\\n\\n"
    assert status == 200
    assert headers == {
        "Content-Type": "text/event-stream; charset=utf-8",
        "Cache-Control": "no-store, no-cache, max-age=0, must-revalidate",
        "X-Content-Type-Options": "nosniff",
    }


def test_service_request_uses_cloudflare_js_request_when_available(monkeypatch):
    import sys
    import types
    import worker

    class FakeRequest:
        @classmethod
        def new(cls, url, init):
            return types.SimpleNamespace(url=url, init=init, method=init["method"], headers=init["headers"], body=init.get("body"))

    class FakeObject:
        @staticmethod
        def fromEntries(value):
            return dict(value)

    js_module = types.ModuleType("js")
    js_module.Request = FakeRequest
    js_module.Object = FakeObject
    ffi_module = types.ModuleType("pyodide.ffi")
    ffi_module.to_js = lambda value, dict_converter: dict_converter(value.items())
    pyodide_module = types.ModuleType("pyodide")
    pyodide_module.ffi = ffi_module
    monkeypatch.setitem(sys.modules, "js", js_module)
    monkeypatch.setitem(sys.modules, "pyodide", pyodide_module)
    monkeypatch.setitem(sys.modules, "pyodide.ffi", ffi_module)

    request = worker._service_request(
        "https://chat/v1/chat",
        method="POST",
        headers={"Authorization": "Bearer test"},
        body='{"message":"hello"}',
    )
    assert request.url == "https://chat/v1/chat"
    assert request.method == "POST"
    assert request.headers == {"Authorization": "Bearer test"}
    assert request.body == '{"message":"hello"}'
    get_request = worker._service_request(
        "https://private/v1/dashboard",
        method="GET",
        headers={"Authorization": "Bearer test"},
    )
    assert get_request.url == "https://private/v1/dashboard"
    assert get_request.method == "GET"
    assert get_request.headers == {"Authorization": "Bearer test"}
    assert get_request.body is None


def test_service_request_uses_structural_fallback_without_js_runtime(monkeypatch):
    import sys
    import types
    import worker

    js_module = types.ModuleType("js")
    pyodide_module = types.ModuleType("pyodide")
    ffi_module = types.ModuleType("pyodide.ffi")
    monkeypatch.setitem(sys.modules, "js", js_module)
    monkeypatch.setitem(sys.modules, "pyodide", pyodide_module)
    monkeypatch.setitem(sys.modules, "pyodide.ffi", ffi_module)

    request = worker._service_request(
        "https://chat/v1/chat",
        method="POST",
        headers={"Content-Type": "application/json"},
        body='{"message":"hello"}',
    )
    assert request.url == "https://chat/v1/chat"
    assert request.method == "POST"
    assert request.headers == {"Content-Type": "application/json"}
    assert request.body == '{"message":"hello"}'

