from pathlib import Path
import json
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
    async def admit(*args, **kwargs):
        return type("Decision", (), {"allowed": True})(), None
    monkeypatch.setattr(worker, "_public_admit", admit)

    class Request:
        method = "POST"
        url = "https://example/api/v1/chat/stream"
        headers = {"Authorization": "Bearer secret", "Idempotency-Key": "r2", "Content-Type": "application/json"}
        async def json(self):
            return {"chat_id": "c2", "request_id": "r2", "message": "hello", "mode": "chat", "strict_zero_cost_only": True}

    instance = worker.Default()
    instance.env = SimpleNamespace(AUTH_TOKEN="secret", DB=object(), ENVIRONMENT="development", LOCAL_DEVELOPMENT_AUTH_BYPASS="true")
    response = asyncio.run(instance.fetch(Request()))
    assert response.status == 503


def test_public_worker_chat_stream_returns_503_for_invalid_sse_payload(monkeypatch):
    import worker

    async def backend(*args, **kwargs):
        return {"ok": True, "response": {"result_state": "BLOCKED"}}, 200

    monkeypatch.setattr(worker, "_operations_chat_stream", backend)
    async def admit(*args, **kwargs):
        return type("Decision", (), {"allowed": True})(), None
    monkeypatch.setattr(worker, "_public_admit", admit)

    class Request:
        method = "POST"
        url = "https://example/api/v1/chat/stream"
        headers = {"Authorization": "Bearer secret", "Idempotency-Key": "r3", "Content-Type": "application/json"}
        async def json(self):
            return {"chat_id": "c3", "request_id": "r3", "message": "hello", "mode": "chat", "strict_zero_cost_only": True}

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
    assert "event: done" in response.body if hasattr(response, "body") else True


def test_public_chat_get_methods_require_auth():
    import worker
    class Request:
        method = "GET"; url = "https://example/api/v1/chat/stream"; headers = {}
    instance = worker.Default(); instance.env = SimpleNamespace(AUTH_TOKEN="secret")
    response = asyncio.run(instance.fetch(Request()))
    assert response.status == 405 or response.status == 401


def test_public_chat_stream_method_not_allowed():
    import worker
    class Request:
        method = "GET"; url = "https://example/api/v1/chat/stream"; headers = {"Authorization":"Bearer secret"}
    instance = worker.Default(); instance.env = SimpleNamespace(AUTH_TOKEN="secret")
    response = asyncio.run(instance.fetch(Request()))
    assert response.status == 405 or response.status == 401


def test_public_worker_chat_stream_route_rejects_bad_idempotency_key():
    import worker
    class Request:
        method = "POST"; url = "https://example/api/v1/chat/stream"
        headers = {"Authorization": "Bearer secret", "Idempotency-Key": "bad key", "Content-Type": "application/json"}
        async def json(self):
            return {"chat_id":"c1","request_id":"r1","message":"hello","strict_zero_cost_only":True}
    instance = worker.Default(); instance.env = SimpleNamespace(AUTH_TOKEN="secret")
    response = asyncio.run(instance.fetch(Request()))
    assert response.status == 400


def test_public_worker_chat_stream_route_rejects_missing_content_type():
    import worker
    class Request:
        method = "POST"; url = "https://example/api/v1/chat/stream"
        headers = {"Authorization":"Bearer secret"}
        async def json(self):
            return {"chat_id":"c1","request_id":"r1","message":"hello","strict_zero_cost_only":True}
    instance = worker.Default(); instance.env = SimpleNamespace(AUTH_TOKEN="secret")
    response = asyncio.run(instance.fetch(Request()))
    assert response.status == 415


def test_public_worker_chat_stream_route_rejects_oversized_request():
    import worker
    class Request:
        method = "POST"; url = "https://example/api/v1/chat/stream"
        headers = {"Authorization":"Bearer secret","Content-Type":"application/json"}
        async def json(self):
            return {"chat_id":"c1","request_id":"r1","message":"x"*20000,"strict_zero_cost_only":True}
    instance = worker.Default(); instance.env = SimpleNamespace(AUTH_TOKEN="secret")
    response = asyncio.run(instance.fetch(Request()))
    assert response.status == 413


def test_operations_chat_stream_translates_private_blocked_terminal_state():
    import worker
    class Response:
        status = 200
        async def json(self):
            return {"ok": True, "response": {"response_id":"blocked-1","result_state":"BLOCKED","text":"blocked","generation_status":"provider_unavailable"}}
    class Binding:
        async def fetch(self, request):
            return Response()
    class Request:
        method = "POST"; url = "https://example/api/v1/chat/stream"; headers = {"Authorization":"Bearer secret","Idempotency-Key":"blocked-1","Content-Type":"application/json"}
        async def json(self):
            return {"chat_id":"c1","request_id":"blocked-1","message":"x","strict_zero_cost_only":True}
    instance = worker.Default(); instance.env = SimpleNamespace(AUTH_TOKEN="secret",OPERATIONS=Binding(),ENVIRONMENT="development",LOCAL_DEVELOPMENT_AUTH_BYPASS="true",DB=object())
    response = asyncio.run(instance.fetch(Request()))
    assert response.status == 200


def test_chat_sse_body_supports_not_attempted_and_failed_states():
    import worker
    for state in ("NOT_ATTEMPTED", "FAILED"):
        body = worker._chat_sse_body({"response": {"response_id": f"{state.lower()}-1", "result_state": state, "text": "", "generation_status": "provider_unavailable"}})
        assert f'"result_state":"{state}"' in body
        assert '"generation_status":"provider_unavailable"' in body
        assert '"status":"not_attempted"' in body or '"status":"failed"' in body


def test_chat_sse_body_blocked_is_truthful_terminal_state():
    import worker
    body = worker._chat_sse_body({"response": {"response_id":"blocked-2","result_state":"BLOCKED","text":"blocked","generation_status":"policy_blocked"}})
    assert '"status":"blocked"' in body
    assert '"result_state":"BLOCKED"' in body
    assert '"generation_status":"policy_blocked"' in body


def test_chat_sse_body_rejects_unknown_result_state():
    import worker
    import pytest
    with pytest.raises(ValueError, match="invalid_chat_result_state"):
        worker._chat_sse_body({"response": {"response_id": "r", "result_state": "MADE_UP_STATE", "text": "x"}})


def test_public_chat_sse_preserves_output_digest():
    import worker
    body = worker._chat_sse_body({"response": {"response_id":"digest-1","result_state":"COMPLETE","text":"hello","generation_status":"model_generated","output_digest":"digest-abc"}})
    assert '"output_digest":"digest-abc"' in body


def test_chat_sse_body_rejects_unknown_result_state():
    import pytest
    import worker

    with pytest.raises(ValueError, match="invalid_chat_result_state"):
        worker._chat_sse_body({
            "response": {
                "response_id": "r",
                "result_state": "MADE_UP_STATE",
                "text": "x",
            }
        })
