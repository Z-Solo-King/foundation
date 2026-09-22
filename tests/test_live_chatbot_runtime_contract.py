import asyncio
import hashlib
from types import SimpleNamespace


def test_chat_headers_support_backend_token_and_optional_idempotency():
    import worker

    class Request:
        headers = {"Idempotency-Key": "chat-1"}

    headers = worker._chat_headers(Request(), SimpleNamespace(CHAT_BACKEND_TOKEN="backend-secret"))
    assert headers["Authorization"] == "Bearer backend-secret"
    assert headers["Idempotency-Key"] == "chat-1"

    class NoKey:
        headers = {}

    headers = worker._chat_headers(NoKey(), SimpleNamespace(CHAT_BACKEND_TOKEN="backend-secret"))
    assert headers["Authorization"] == "Bearer backend-secret"
    assert "Idempotency-Key" not in headers


def test_anonymous_chat_helpers_cover_authenticated_and_anonymous_subjects():
    import worker

    assert worker._anonymous_chat_enabled(SimpleNamespace(PUBLIC_CHAT_ANONYMOUS="true")) is True
    assert worker._anonymous_chat_enabled(SimpleNamespace(PUBLIC_CHAT_ANONYMOUS="false")) is False

    authenticated = SimpleNamespace(headers={"Authorization": "Bearer user-token", "CF-Connecting-IP": "1.2.3.4", "User-Agent": "ua"})
    assert worker._public_chat_subject(authenticated) == hashlib.sha256(b"user-token").hexdigest()

    anonymous = SimpleNamespace(headers={"CF-Connecting-IP": "1.2.3.4", "User-Agent": "ua"})
    expected = hashlib.sha256(b"anonymous|1.2.3.4|ua").hexdigest()
    assert worker._public_chat_subject(anonymous) == expected


def test_anonymous_chat_route_uses_public_admission_without_client_auth(monkeypatch):
    import worker

    async def backend(*args, **kwargs):
        return {"ok": True, "response": {"response_id": "r1", "result_state": "PARTIAL", "text": "hello"}}, 200

    monkeypatch.setattr(worker, "_operations_chat", backend)

    class Request:
        method = "POST"
        url = "https://example/api/v1/chat"
        headers = {"Content-Type": "application/json", "CF-Connecting-IP": "1.2.3.4", "User-Agent": "ua"}

        async def json(self):
            return {"chat_id": "c1", "request_id": "r1", "message": "hello", "mode": "chat", "strict_zero_cost_only": True}

    entry = worker.Default()
    entry.env = SimpleNamespace(
        DB=None,
        ENVIRONMENT="development",
        LOCAL_DEVELOPMENT_AUTH_BYPASS="true",
        AUTH_TOKEN="secret",
        PUBLIC_CHAT_ANONYMOUS="true",
    )
    response = asyncio.run(entry.fetch(Request()))
    assert response.status == 200


def test_anonymous_stream_route_uses_public_admission_without_client_auth(monkeypatch):
    import worker

    async def backend(*args, **kwargs):
        return {"ok": False, "error": "chat_backend_unavailable"}, 503

    async def admit(*args, **kwargs):
        return type("Decision", (), {"allowed": True})(), None

    monkeypatch.setattr(worker, "_operations_chat_stream", backend)
    monkeypatch.setattr(worker, "_public_admit", admit)

    class Request:
        method = "POST"
        url = "https://example/api/v1/chat/stream"
        headers = {"Content-Type": "application/json", "CF-Connecting-IP": "5.6.7.8", "User-Agent": "ua"}

        async def json(self):
            return {"chat_id": "c2", "request_id": "r2", "message": "hello", "mode": "chat", "strict_zero_cost_only": True}

    entry = worker.Default()
    entry.env = SimpleNamespace(
        DB=object(),
        ENVIRONMENT="production",
        AUTH_TOKEN="secret",
        PUBLIC_CHAT_ANONYMOUS="true",
    )
    response = asyncio.run(entry.fetch(Request()))
    assert response.status == 503
