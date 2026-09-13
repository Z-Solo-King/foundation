from types import SimpleNamespace

import pytest

import worker


class Response:
    def __init__(self, payload, status=200):
        self.status = status
        self._payload = payload

    async def json(self):
        return self._payload


class Control:
    def __init__(self):
        self.calls = []

    async def fetch(self, url, init=None):
        self.calls.append((url, init))
        return Response({"ok": True, "status": "ok", "checks": []})


@pytest.mark.asyncio
async def test_chatbot_infrastructure_operation_dispatches_to_private_verifier():
    control = Control()
    body, status = await worker._control_plane_chatbot_diagnostic(
        SimpleNamespace(CONTROL_PLANE=control),
        {"operation": "infrastructure_verify"},
    )
    assert status == 200
    assert body["ok"] is True
    assert control.calls[0][0].endswith("/v1/diagnostics/infrastructure")


@pytest.mark.asyncio
async def test_non_infrastructure_chatbot_operation_keeps_routing_diagnostic():
    control = Control()
    body, status = await worker._control_plane_chatbot_diagnostic(
        SimpleNamespace(CONTROL_PLANE=control),
        {"operation": "knowledge", "question": "Explain testing"},
    )
    assert status == 200
    assert body["ok"] is True
    assert control.calls[0][0].endswith("/v1/diagnostics/chatbot")
