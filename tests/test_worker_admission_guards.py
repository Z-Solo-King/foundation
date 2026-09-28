import pytest


class Request:
    def __init__(self, url, payload, headers):
        self.method = "POST"
        self.url = url
        self.headers = headers

        self._payload = payload

    async def json(self):
        return self._payload


@pytest.mark.asyncio
async def test_stream_rejects_missing_authenticated_subject_in_production(monkeypatch):
    import worker

    monkeypatch.setattr(worker, "_authorized", lambda request, env: True)
    monkeypatch.setattr(worker, "_subject_or_local", lambda request, env: None)

    entry = worker.Default()
    entry.env = type("Env", (), {"ENVIRONMENT": "production"})()
    response = await entry.fetch(
        Request(
            "https://x/api/v1/chat/stream",
            {"chat_id": "c", "request_id": "r", "message": "hello", "mode": "chat", "strict_zero_cost_only": True},
            {"Content-Type": "application/json"},
        )
    )
    assert response.status == 401


@pytest.mark.asyncio
async def test_stream_rejects_invalid_idempotency_key_before_admission(monkeypatch):
    import worker

    monkeypatch.setattr(worker, "_authorized", lambda request, env: True)
    monkeypatch.setattr(worker, "_subject_or_local", lambda request, env: "subject-1")
    monkeypatch.setattr(worker, "_idempotency_key", lambda request, default=None: None)

    entry = worker.Default()
    entry.env = type("Env", (), {})()
    response = await entry.fetch(
        Request(
            "https://x/api/v1/chat/stream",
            {"chat_id": "c", "request_id": "r", "message": "hello", "mode": "chat", "strict_zero_cost_only": True},
            {"Content-Type": "application/json", "Idempotency-Key": "bad key"},
        )
    )
    assert response.status == 400


@pytest.mark.asyncio
async def test_chat_rejects_missing_authenticated_subject_in_production(monkeypatch):
    import worker

    monkeypatch.setattr(worker, "_authorized", lambda request, env: True)
    monkeypatch.setattr(worker, "_subject_or_local", lambda request, env: None)

    entry = worker.Default()
    entry.env = type("Env", (), {"ENVIRONMENT": "production"})()
    response = await entry.fetch(
        Request(
            "https://x/api/v1/chat",
            {"chat_id": "c", "request_id": "r", "message": "hello", "mode": "chat", "strict_zero_cost_only": True},
            {"Content-Type": "application/json"},
        )
    )
    assert response.status == 401


@pytest.mark.asyncio
async def test_research_rejects_invalid_idempotency_key_before_admission(monkeypatch):
    import worker

    monkeypatch.setattr(worker, "_authorized", lambda request, env: True)
    monkeypatch.setattr(worker, "_subject_or_local", lambda request, env: "subject-1")
    monkeypatch.setattr(worker, "_idempotency_key", lambda request, default=None: None)

    entry = worker.Default()
    entry.env = type("Env", (), {})()
    response = await entry.fetch(
        Request(
            "https://x/api/v1/research",
            {"question": "q", "strict_zero_cost_only": True},
            {"Content-Type": "application/json", "Idempotency-Key": "bad key"},
        )
    )
    assert response.status == 400
