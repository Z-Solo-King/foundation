from types import SimpleNamespace

import pytest

import worker


class Request:
    def __init__(self, payload, headers=None):
        self.method = "POST"
        self.url = "https://example.test/api/v1/chatbot/diagnostic"
        self._payload = payload
        self.headers = headers or {}

    async def json(self):
        return self._payload


class FakeResponse:
    def __init__(self, payload, status):
        self._payload = payload
        self.status = status

    async def json(self):
        return self._payload


class FakeOperations:
    def __init__(self, payload, status):
        self.payload = payload
        self.status = status

    async def fetch(self, request):
        return FakeResponse(self.payload, self.status)


@pytest.mark.asyncio
async def test_public_chatbot_infrastructure_route_requires_auth(monkeypatch):
    async def verify(env):
        return {"ok": True, "status": "ok", "checks": [{"name": "cloudflare_d1", "ok": True}]}, 200

    monkeypatch.setattr(worker, "_public_infrastructure_verify", verify)
    entry = worker.Default()
    entry.env = SimpleNamespace(
        ENVIRONMENT="production",
        AUTH_TOKEN="secret",
        OPERATIONS=FakeOperations(
            {
                "ok": True,
                "runtime_status": "ok",
                "runtime_checks": [{"name": "chat_backend", "ok": True}],
                "chatbot": {"allowed": True},
            },
            200,
        ),
        CONTROL_PLANE=None,
    )

    unauthorized = await entry.fetch(Request({"operation": "infrastructure_verify_public_test"}))
    assert "unauthorized" in str(unauthorized).lower()

    authorized = await entry.fetch(
        Request(
            {"operation": "infrastructure_verify_public_test"},
            {"Authorization": "Bearer secret", "Content-Type": "application/json"},
        )
    )
    assert '"ok": true' in str(authorized).lower()


@pytest.mark.asyncio
async def test_public_chatbot_diagnostic_uses_private_result_fail_closed(monkeypatch):
    async def public_verify(env):
        return {"ok": True, "status": "ok", "checks": [{"name": "cloudflare_d1", "ok": True}]}, 200

    monkeypatch.setattr(worker, "_public_infrastructure_verify", public_verify)

    entry = worker.Default()
    entry.env = SimpleNamespace(
        ENVIRONMENT="production",
        AUTH_TOKEN="secret",
        OPERATIONS=FakeOperations(
            {
                "ok": False,
                "runtime_status": "degraded",
                "runtime_checks": [{"name": "chat_backend", "ok": False}],
                "chatbot": {"allowed": False},
                "error": "chat_backend_unavailable",
            },
            503,
        ),
        CONTROL_PLANE=None,
    )

    response = await entry.fetch(
        Request(
            {"operation": "infrastructure_verify_public_test"},
            {"Authorization": "Bearer secret", "Content-Type": "application/json"},
        )
    )
    text = str(response).lower()
    assert '"name": "public_chatbot"' in text
    assert '"ok": false' in text
    assert '"status": "degraded"' in text
    assert "chat_backend_unavailable" in text
