import asyncio
import hashlib
from pathlib import Path
from types import SimpleNamespace

import worker

ROOT = Path(__file__).parents[1]


def test_chat_headers_covers_backend_and_auth_fallbacks():
    class Request:
        headers = {"Idempotency-Key": "k1"}

    headers = worker._chat_headers(Request(), SimpleNamespace(CHAT_BACKEND_TOKEN="backend", AUTH_TOKEN="auth"))
    assert headers["Authorization"] == "Bearer backend"
    assert headers["Idempotency-Key"] == "k1"

    headers = worker._chat_headers(type("R", (), {"headers": {}})(), SimpleNamespace(CHAT_BACKEND_TOKEN="", AUTH_TOKEN="auth"))
    assert headers["Authorization"] == "Bearer auth"

    headers = worker._chat_headers(type("R", (), {"headers": {}})(), SimpleNamespace(CHAT_BACKEND_TOKEN="", AUTH_TOKEN=""))
    assert "Authorization" not in headers


def test_anonymous_chat_helpers_cover_true_false_authenticated_and_anonymous(monkeypatch):
    assert worker._anonymous_chat_enabled(SimpleNamespace(PUBLIC_CHAT_ANONYMOUS="TRUE")) is True
    assert worker._anonymous_chat_enabled(SimpleNamespace(PUBLIC_CHAT_ANONYMOUS="false")) is False

    monkeypatch.setattr(worker, "authenticated_subject_fingerprint", lambda request: hashlib.sha256(b"user").hexdigest())
    authenticated = SimpleNamespace(headers={"Authorization": "Bearer user"})
    assert worker._public_chat_subject(authenticated) == hashlib.sha256(b"user").hexdigest()

    monkeypatch.setattr(worker, "authenticated_subject_fingerprint", lambda request: "")
    anonymous = SimpleNamespace(headers={"CF-Connecting-IP": "1.2.3.4", "User-Agent": "ua"})
    assert worker._public_chat_subject(anonymous) == hashlib.sha256(b"anonymous|1.2.3.4|ua").hexdigest()


def _fake_payload():
    return {
        "chat_id": "chat-1",
        "request_id": "request-1",
        "message": "hello",
        "mode": "chat",
        "strict_zero_cost_only": True,
    }


class _Request:
    method = "POST"
    headers = {
        "Content-Type": "application/json",
        "CF-Connecting-IP": "1.2.3.4",
        "User-Agent": "pytest",
    }
    url = "https://public.example/api/v1/chat"

    async def json(self):
        return _fake_payload()


def test_anonymous_chat_route_executes_public_admission_and_backend(monkeypatch):
    class FakeChatRequest:
        def __init__(self, **kwargs):
            self.request_id = kwargs["request_id"]

        def validate(self):
            return None

    async def admit(*args, **kwargs):
        return object(), None

    async def backend(*args, **kwargs):
        return {"ok": True, "response": {"result_state": "PARTIAL", "text": "hello"}}, 200

    monkeypatch.setattr(worker, "ChatRequest", FakeChatRequest)
    monkeypatch.setattr(worker, "_public_admit", admit)
    monkeypatch.setattr(worker, "_admission_response", lambda decision: None)
    monkeypatch.setattr(worker, "_operations_chat", backend)

    entry = worker.Default()
    entry.env = SimpleNamespace(
        AUTH_TOKEN="admin",
        PUBLIC_CHAT_ANONYMOUS="true",
        ENVIRONMENT="production",
        DB=None,
    )
    response = asyncio.run(entry.fetch(_Request()))
    assert response.status == 200


def test_anonymous_stream_route_executes_subject_and_upstream_failure(monkeypatch):
    class FakeChatRequest:
        def __init__(self, **kwargs):
            self.request_id = kwargs["request_id"]

        def validate(self):
            return None

    async def admit(*args, **kwargs):
        return object(), None

    async def backend(*args, **kwargs):
        return {"ok": False, "error": "chat_backend_unavailable"}, 503

    monkeypatch.setattr(worker, "ChatRequest", FakeChatRequest)
    monkeypatch.setattr(worker, "_public_admit", admit)
    monkeypatch.setattr(worker, "_admission_response", lambda decision: None)
    monkeypatch.setattr(worker, "_operations_chat_stream", backend)

    request = _Request()
    request.url = "https://public.example/api/v1/chat/stream"

    entry = worker.Default()
    entry.env = SimpleNamespace(
        AUTH_TOKEN="admin",
        PUBLIC_CHAT_ANONYMOUS="true",
        ENVIRONMENT="production",
        DB=None,
    )
    response = asyncio.run(entry.fetch(request))
    assert response.status == 503
