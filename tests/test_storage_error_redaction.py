import asyncio
import json
from types import SimpleNamespace


def test_public_research_persistence_error_is_redacted(monkeypatch):
    import worker

    captured = {}

    class Response:
        def __init__(self, body, *, status=200, headers=None):
            captured["body"] = body
            self.status = status

    class FailingDB:
        def prepare(self, sql):
            raise RuntimeError("db down with private endpoint details")

    class Request:
        method = "GET"
        url = "https://example/api/v1/research/run-1"
        headers = {"Authorization": "Bearer secret"}

    monkeypatch.setattr(worker, "Response", Response)
    entry = worker.Default()
    entry.env = SimpleNamespace(
        DB=FailingDB(),
        AUTH_TOKEN="secret",
        ENVIRONMENT="production",
    )

    response = asyncio.run(entry.fetch(Request()))

    assert response.status == 503
    assert json.loads(captured["body"]) == {
        "ok": False,
        "error": "persistence_unavailable",
    }
