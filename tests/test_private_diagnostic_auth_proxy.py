import asyncio
from types import SimpleNamespace

from worker import _operations_chatbot_diagnostic


class Request:
    def __init__(self, authorization):
        self.headers = {"Authorization": authorization}


class Response:
    status = 200

    async def json(self):
        return {"ok": True, "chatbot": {"allowed": True}, "runtime_status": "ok", "runtime_checks": [{"name": "d1_memory_store", "ok": True}]}


class Binding:
    def __init__(self):
        self.requests = []

    async def fetch(self, request):
        self.requests.append(request)
        return Response()


def test_private_chatbot_diagnostic_forwards_bearer_auth():
    binding = Binding()
    env = SimpleNamespace(OPERATIONS=binding)
    result, status = asyncio.run(
        _operations_chatbot_diagnostic(
            env,
            Request("Bearer secret"),
        )
    )
    assert status == 200
    assert result["ok"] is True
    assert len(binding.requests) == 1
    assert binding.requests[0].headers["Authorization"] == "Bearer secret"


def test_persistence_seed_operation_is_forwarded_verbatim():
    binding = Binding()
    env = SimpleNamespace(OPERATIONS=binding)
    result, status = asyncio.run(
        _operations_chatbot_diagnostic(
            env,
            Request("Bearer secret"),
            operation="persistence_seed",
        )
    )
    assert status == 200
    assert result["ok"] is True
    assert len(binding.requests) == 1


def test_default_diagnostic_operation_remains_infrastructure_verify():
    binding = Binding()
    env = SimpleNamespace(OPERATIONS=binding)
    result, status = asyncio.run(
        _operations_chatbot_diagnostic(env, Request("Bearer secret"))
    )
    assert status == 200
    assert result["ok"] is True
    assert len(binding.requests) == 1
