import pytest

from backend.admission import AdmissionPolicy, AdmissionRoute
from backend.admission_store import D1AdmissionStore, ROUTE_COST_UNITS


class FakeStatement:
    def __init__(self, query):
        self.query = query
        self.args = ()

    def bind(self, *args):
        self.args = args
        return self

    async def run(self):
        return {"meta": {"changes": 1}}

    async def first(self):
        return {
            "subject_requests": 0,
            "global_requests": 0,
            "subject_concurrent": 0,
            "global_concurrent": 0,
        }


class FakeDB:
    def __init__(self):
        self.queries = []

    def prepare(self, query):
        self.queries.append(query)
        return FakeStatement(query)


@pytest.mark.asyncio
async def test_d1_store_admits_with_existing_admission_policy():
    db = FakeDB()
    store = D1AdmissionStore(db)
    decision, lease = await store.acquire(
        subject_fingerprint="subject-1",
        route=AdmissionRoute.RESEARCH,
        policy=AdmissionPolicy(),
        event_id="event-1",
        now=120,
    )
    assert decision.allowed is True
    assert lease is not None
    assert lease.event_id == "event-1"
    assert lease.cost_units == 5
    assert any("public_admission_events" in query for query in db.queries)


@pytest.mark.asyncio
async def test_d1_store_release_is_idempotent_at_statement_level():
    db = FakeDB()
    store = D1AdmissionStore(db)
    decision, lease = await store.acquire(
        subject_fingerprint="subject-1",
        route=AdmissionRoute.CHAT,
        policy=AdmissionPolicy(),
        event_id="event-1",
        now=120,
    )
    assert decision.allowed and lease is not None
    await store.release(lease)
    await store.release(lease)
    assert sum("UPDATE public_admission_events" in query for query in db.queries) == 2


def test_route_cost_classes_are_explicit_and_bounded():
    policy = AdmissionPolicy()
    assert set(ROUTE_COST_UNITS) == {
        AdmissionRoute.CHEAP_READ,
        AdmissionRoute.CHAT,
        AdmissionRoute.RESEARCH,
        AdmissionRoute.STREAM,
    }
    assert ROUTE_COST_UNITS[AdmissionRoute.RESEARCH] > ROUTE_COST_UNITS[AdmissionRoute.CHAT]
    policy.validate()


def test_public_worker_rejects_expensive_paths_before_upstream_call_source_contract():
    source = open("worker.py", encoding="utf-8").read()
    assert "AdmissionRoute.CHAT" in source
    assert "AdmissionRoute.RESEARCH" in source
    assert "_operations_chat(self.env" in source
    assert "_operations_chat_stream(self.env" in source
    assert "await _public_admit" in source


class Request:
    def __init__(self, method, url, payload=None, headers=None):
        self.method = method
        self.url = url
        self._payload = payload
        self.headers = headers or {}

    async def json(self):
        return self._payload


class AdmissionLeaseTracker:
    def __init__(self):
        self.released = []

    async def release(self, lease):
        self.released.append(lease)


class Persistence:
    def __init__(self):
        self.created = []

    async def create_run(self, run_id, request):
        self.created.append(run_id)
        return run_id


def accepted_admission(lease):
    from backend.admission import AdmissionDecision, AdmissionOutcome
    return AdmissionDecision(
        AdmissionOutcome.ACCEPTED,
        AdmissionRoute.CHAT,
        True,
        "accepted",
    ), lease


@pytest.mark.asyncio
async def test_worker_chat_and_stream_release_admission_lease(monkeypatch):
    import worker

    tracker = AdmissionLeaseTracker()
    lease = object()
    monkeypatch.setattr(worker, "D1AdmissionStore", lambda db: tracker)
    async def admit(*args, **kwargs): return accepted_admission(lease)
    monkeypatch.setattr(worker, "_public_admit", admit)

    env = type("Env", (), {"AUTH_TOKEN": "secret", "DB": object()})()
    entry = worker.Default()
    entry.env = env
    payload = {
        "chat_id": "chat-1",
        "request_id": "request-1",
        "message": "hello",
        "mode": "chat",
        "strict_zero_cost_only": True,
    }

    async def chat_backend(env, payload, request):
        return {"ok": True, "response": {"text": "ok"}}, 200

    class Upstream:
        body = "event: start\\n\\n"
        status = 200

    async def stream_backend(env, payload, request):
        return Upstream(), None, 200

    monkeypatch.setattr(worker, "_operations_chat", chat_backend)
    monkeypatch.setattr(worker, "_operations_chat_stream", stream_backend)

    chat_response = await entry.fetch(
        Request("POST", "https://x/api/v1/chat", payload, {"Authorization": "Bearer secret", "Content-Type": "application/json"})
    )
    assert chat_response.status == 200

    stream_response = await entry.fetch(
        Request("POST", "https://x/api/v1/chat/stream", payload, {"Authorization": "Bearer secret", "Content-Type": "application/json"})
    )
    assert stream_response.status == 200
    assert tracker.released == [lease, lease]


@pytest.mark.asyncio
async def test_worker_research_rejected_result_releases_admission_lease(monkeypatch):
    import worker

    tracker = AdmissionLeaseTracker()
    lease = object()
    monkeypatch.setattr(worker, "D1AdmissionStore", lambda db: tracker)
    async def admit(*args, **kwargs): return accepted_admission(lease)
    monkeypatch.setattr(worker, "_public_admit", admit)
    monkeypatch.setattr(
        worker,
        "submit_research",
        lambda request: type("Result", (), {"ok": False, "error": "rejected"})(),
    )

    env = type("Env", (), {"AUTH_TOKEN": "secret"})()
    entry = worker.Default()
    entry.env = env
    response = await entry.fetch(
        Request(
            "POST",
            "https://x/api/v1/research",
            {"question": "q", "strict_zero_cost_only": True},
            {"Authorization": "Bearer secret", "Content-Type": "application/json"},
        )
    )
    assert response.status == 400
    assert tracker.released == [lease]


@pytest.mark.asyncio
async def test_worker_research_uses_legacy_create_run_fallback(monkeypatch):
    import worker

    tracker = AdmissionLeaseTracker()
    lease = object()
    persistence = Persistence()
    monkeypatch.setattr(worker, "D1AdmissionStore", lambda db: tracker)
    async def admit(*args, **kwargs): return accepted_admission(lease)\n    monkeypatch.setattr(worker, "_public_admit", admit)
    monkeypatch.setattr(
        worker,
        "submit_research",
        lambda request: type(
            "Result",
            (),
            {"ok": True, "run_id": "run-legacy", "metadata": {"mode": "test"}},
        )(),
    )
    monkeypatch.setattr(worker, "CloudflarePersistence", lambda env: persistence)

    env = type("Env", (), {"AUTH_TOKEN": "secret"})()
    entry = worker.Default()
    entry.env = env
    response = await entry.fetch(
        Request(
            "POST",
            "https://x/api/v1/research",
            {"question": "q", "strict_zero_cost_only": True},
            {"Authorization": "Bearer secret", "Content-Type": "application/json"},
        )
    )
    assert response.status == 200
    assert persistence.created == ["run-legacy"]
    assert tracker.released == [lease]
