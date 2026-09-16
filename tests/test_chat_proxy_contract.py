import asyncio
from types import SimpleNamespace


def test_chat_proxy_fails_closed_without_operations_binding():
    import worker

    class Request:
        headers = {}

    payload, status = asyncio.run(worker._operations_chat(SimpleNamespace(), {"message": "x"}, Request()))
    assert status == 503
    assert payload["error"] == "chat_backend_unavailable"


def test_chat_proxy_forwards_auth_and_idempotency():
    import worker

    class Response:
        status = 200

        async def json(self):
            return {"ok": True, "response": {"text": "hello"}}

    class Binding:
        def __init__(self):
            self.calls = []

        async def fetch(self, url, options):
            self.calls.append((url, options))
            return Response()

    class Request:
        headers = {"Authorization": "Bearer user", "Idempotency-Key": "req-1"}

    binding = Binding()
    payload, status = asyncio.run(worker._operations_chat(SimpleNamespace(OPERATIONS=binding), {"message": "hello"}, Request()))
    assert status == 200
    assert payload["ok"] is True
    url, options = binding.calls[0]
    assert url == "https://chat/v1/chat"
    assert options["headers"]["Authorization"] == "Bearer user"
    assert options["headers"]["Idempotency-Key"] == "req-1"


def test_chat_stream_proxy_preserves_sse_response():
    import worker

    class Body:
        pass

    class Response:
        status = 200
        body = Body()

    class Binding:
        async def fetch(self, url, options):
            assert url == "https://chat/v1/chat/stream"
            assert options["headers"]["Idempotency-Key"] == "req-2"
            return Response()

    class Request:
        headers = {"Authorization": "Bearer user", "Idempotency-Key": "req-2"}

    upstream, body, status = asyncio.run(worker._operations_chat(SimpleNamespace(OPERATIONS=Binding()), {"message": "hello"}, Request(), stream=True))
    assert upstream.status == 200
    assert body is None
    assert status == 200


def test_public_worker_chat_route_requires_auth_and_validates_payload():
    import worker

    class Request:
        method = "POST"
        url = "https://example/api/v1/chat"

        def __init__(self, headers, body):
            self.headers = headers
            self._body = body

        async def json(self):
            return self._body

    unauthorized = worker.Default()
    unauthorized.env = SimpleNamespace(AUTH_TOKEN="secret")
    response = asyncio.run(unauthorized.fetch(Request({}, {"message": "hello"})))
    assert response.status == 401

    invalid = worker.Default()
    invalid.env = SimpleNamespace(AUTH_TOKEN="secret")
    response = asyncio.run(invalid.fetch(Request({"Authorization": "Bearer secret"}, {"message": "hello"})))
    assert response.status == 400
