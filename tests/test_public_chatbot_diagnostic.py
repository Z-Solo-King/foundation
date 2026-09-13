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


@pytest.mark.asyncio
async def test_public_chatbot_infrastructure_route_requires_auth(monkeypatch):
    async def verify(env):
        return {"ok": True, "status": "ok", "checks": [{"name": "public_chatbot", "ok": True}]}, 200

    monkeypatch.setattr(worker, "_public_infrastructure_verify", verify)
    entry = worker.Default()
    entry.env = SimpleNamespace(
        ENVIRONMENT="production",
        AUTH_TOKEN="secret",
        CONTROL_PLANE=None,
    )

    unauthorized = await entry.fetch(Request({"operation": "infrastructure_verify_public_test"}))
    assert "unauthorized" in str(unauthorized).lower()

    authorized = await entry.fetch(
        Request(
            {"operation": "infrastructure_verify_public_test"},
            {"Authorization": "Bearer secret"},
        )
    )
    assert "ok" in str(authorized)
