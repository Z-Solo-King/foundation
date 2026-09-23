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


def test_persistence_verify_forwards_sentinel_identity():
    binding = Binding()
    env = SimpleNamespace(OPERATIONS=binding)
    result, status = asyncio.run(
        _operations_chatbot_diagnostic(
            env,
            Request("Bearer secret"),
            operation="persistence_verify",
            payload={"operation": "persistence_verify", "sentinel_id": "sentinel-123"},
        )
    )
    assert status == 200
    assert result["ok"] is True
    assert len(binding.requests) == 1
    forwarded = __import__("json").loads(binding.requests[0].body)
    assert forwarded["operation"] == "persistence_verify"
    assert forwarded["sentinel_id"] == "sentinel-123"


def test_persistence_verify_omits_empty_sentinel_identity():
    binding = Binding()
    env = SimpleNamespace(OPERATIONS=binding)
    result, status = asyncio.run(
        _operations_chatbot_diagnostic(
            env,
            Request("Bearer secret"),
            operation="persistence_verify",
            payload={"operation": "persistence_verify", "sentinel_id": ""},
        )
    )
    assert status == 200
    assert result["ok"] is True
    forwarded = __import__("json").loads(binding.requests[0].body)
    assert "sentinel_id" not in forwarded


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


class PersistenceResponse:
    status = 200

    async def json(self):
        return {
            "ok": True,
            "status": 200,
            "sentinel_id": "sentinel",
            "memory_persisted_across_version": True,
            "replay_nonce_rejected_after_version_change": True,
            "cleanup_status": 200,
        }


def test_persistence_diagnostic_preserves_private_response_contract():
    binding = Binding()

    async def fetch_persistence(request):
        binding.requests.append(request)
        return PersistenceResponse()

    binding.fetch = fetch_persistence
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
    assert result["sentinel_id"] == "sentinel"
    assert result["memory_persisted_across_version"] is True
