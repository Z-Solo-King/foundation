import pytest

from backend.admission import AdmissionPolicy, AdmissionRoute
from backend.admission_store import D1AdmissionStore, ROUTE_COST_UNITS, _insert_new_admission


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
        if "SELECT EVENT_ID" in self.query.upper():
            return None
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


@pytest.mark.asyncio
async def test_concurrent_insert_loss_replays_existing_protected_event():
    from backend.admission import AdmissionDecision, AdmissionOutcome

    db = IdempotentAdmissionDB()
    existing = {
        "event_id": "protected-race",
        "window_start": 120,
        "subject_fingerprint": "subject-1",
        "route": "chat",
        "cost_units": 2,
        "lease_expires_at": 180,
        "released_at": None,
    }
    db.events["protected-race"] = existing
    store = D1AdmissionStore(db)

    async def lost_insert(**_kwargs):
        return False

    store._insert_if_admissible = lost_insert
    decision = AdmissionDecision(
        AdmissionOutcome.ACCEPTED,
        AdmissionRoute.CHAT,
        True,
        "admission accepted",
    )

    result, lease = await _insert_new_admission(
        store,
        decision,
        event_id="protected-race",
        window_start=120,
        subject_fingerprint="subject-1",
        route=AdmissionRoute.CHAT,
        cost_units=2,
        expires_at=181,
        now=121,
        policy=AdmissionPolicy(),
    )

    assert result.outcome is AdmissionOutcome.ACCEPTED
    assert result.allowed is True
    assert lease is None


def test_public_admission_insert_is_idempotent_source_contract():
    source = open("backend/admission_store.py", encoding="utf-8").read()
    assert "INSERT OR IGNORE INTO public_admission_events" in source


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
async def test_concurrent_same_event_id_rechecks_existing_event(monkeypatch):
    db = FakeDB()
    store = D1AdmissionStore(db)

    existing = {
        "event_id": "event-race",
        "subject_fingerprint": "subject-1",
        "route": "chat",
        "window_start": 120,
        "lease_expires_at": 180,
        "released_at": None,
    }

    class ExistingDB(FakeDB):
        def prepare(self, query):
            if "SELECT event_id, window_start" in query:
                statement = FakeStatement(query)
                async def first():
                    return existing
                statement.first = first
                return statement
            return super().prepare(query)

    store.db = ExistingDB()
    async def lost_insert(*args, **kwargs):
        return False
    monkeypatch.setattr(store, "_insert_if_admissible", lost_insert)

    decision, lease = await store.acquire(
        subject_fingerprint="subject-1",
        route=AdmissionRoute.CHAT,
        policy=AdmissionPolicy(),
        event_id="event-race",
        now=120,
    )

    assert decision.allowed is True
    assert decision.outcome.value == "accepted"
    assert lease is None


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
        return {"ok": True, "response": {"response_id": "chat-r1", "result_state": "PARTIAL", "text": "ok", "generation_status": "deterministic_fallback"}}, 200

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

    env = type("Env", (), {"AUTH_TOKEN": "secret", "DB": object()})()
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
    async def admit(*args, **kwargs):
        return accepted_admission(lease)
    monkeypatch.setattr(worker, "_public_admit", admit)
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

    env = type("Env", (), {"AUTH_TOKEN": "secret", "DB": object()})()
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


def test_admission_response_emits_retry_after_header():
    import worker
    from backend.admission import AdmissionDecision, AdmissionOutcome

    response = worker._admission_response(
        AdmissionDecision(
            AdmissionOutcome.RATE_LIMITED,
            AdmissionRoute.RESEARCH,
            False,
            "rate limited",
            retry_after_seconds=7,
        )
    )
    assert response.status == 429
    assert response.headers["Retry-After"] == "7"


@pytest.mark.asyncio
async def test_worker_chat_denied_admission_stops_before_upstream(monkeypatch):
    import worker
    from backend.admission import AdmissionDecision, AdmissionOutcome

    async def deny(*args, **kwargs):
        return AdmissionDecision(
            AdmissionOutcome.RATE_LIMITED,
            AdmissionRoute.CHAT,
            False,
            "rate limited",
            retry_after_seconds=3,
        ), None

    called = False

    async def backend(*args, **kwargs):
        nonlocal called
        called = True
        return {"ok": True}, 200

    monkeypatch.setattr(worker, "_public_admit", deny)
    monkeypatch.setattr(worker, "_operations_chat", backend)

    env = type("Env", (), {"AUTH_TOKEN": "secret", "DB": object()})()
    entry = worker.Default()
    entry.env = env
    response = await entry.fetch(
        Request(
            "POST",
            "https://x/api/v1/chat",
            {"chat_id": "c", "request_id": "r", "message": "hello", "mode": "chat", "strict_zero_cost_only": True},
            {"Authorization": "Bearer secret", "Content-Type": "application/json"},
        )
    )
    assert response.status == 429
    assert response.headers["Retry-After"] == "3"
    assert called is False


@pytest.mark.asyncio
async def test_worker_research_denied_admission_stops_before_submit(monkeypatch):
    import worker
    from backend.admission import AdmissionDecision, AdmissionOutcome

    async def deny(*args, **kwargs):
        return AdmissionDecision(
            AdmissionOutcome.CONCURRENCY_LIMITED,
            AdmissionRoute.RESEARCH,
            False,
            "concurrency limited",
            retry_after_seconds=4,
        ), None

    called = False

    def submit(*args, **kwargs):
        nonlocal called
        called = True
        return type("Result", (), {"ok": True, "run_id": "run", "metadata": {}})()

    monkeypatch.setattr(worker, "_public_admit", deny)
    monkeypatch.setattr(worker, "submit_research", submit)

    env = type("Env", (), {"AUTH_TOKEN": "secret", "DB": object()})()
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
    assert response.status == 429
    assert response.headers["Retry-After"] == "4"
    assert called is False


@pytest.mark.asyncio
async def test_worker_research_rejected_result_handles_missing_admission_lease(monkeypatch):
    import worker

    async def admit(*args, **kwargs):
        return accepted_admission(None)

    monkeypatch.setattr(worker, "_public_admit", admit)
    monkeypatch.setattr(
        worker,
        "submit_research",
        lambda request: type("Result", (), {"ok": False, "error": "rejected"})(),
    )

    env = type("Env", (), {"AUTH_TOKEN": "secret", "DB": object()})()
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


@pytest.mark.asyncio
async def test_worker_research_success_handles_missing_admission_lease(monkeypatch):
    import worker

    async def admit(*args, **kwargs):
        return accepted_admission(None)

    monkeypatch.setattr(worker, "_public_admit", admit)
    monkeypatch.setattr(
        worker,
        "submit_research",
        lambda request: type(
            "Result",
            (),
            {"ok": True, "run_id": "run-no-lease", "metadata": {"mode": "test"}},
        )(),
    )
    persistence = Persistence()
    monkeypatch.setattr(worker, "CloudflarePersistence", lambda env: persistence)

    env = type("Env", (), {"AUTH_TOKEN": "secret", "DB": object()})()
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
    assert persistence.created == ["run-no-lease"]


@pytest.mark.asyncio
async def test_d1_store_rejects_negative_now():
    store = D1AdmissionStore(FakeDB())
    with pytest.raises(ValueError, match="now must be non-negative"):
        await store.acquire(
            subject_fingerprint="subject-1",
            route=AdmissionRoute.RESEARCH,
            policy=AdmissionPolicy(),
            event_id="event-1",
            now=-1,
        )


@pytest.mark.asyncio
async def test_d1_store_returns_denied_decision_from_authoritative_snapshot(monkeypatch):
    from backend.admission import AdmissionSnapshot

    store = D1AdmissionStore(FakeDB())
    policy = AdmissionPolicy()

    async def snapshot(**kwargs):
        return AdmissionSnapshot(
            authority_available=True,
            global_requests=policy.max_requests_global,
        )

    monkeypatch.setattr(store, "_snapshot", snapshot)
    decision, lease = await store.acquire(
        subject_fingerprint="subject-1",
        route=AdmissionRoute.RESEARCH,
        policy=policy,
        event_id="event-1",
        now=120,
    )
    assert decision.allowed is False
    assert decision.outcome.value == "rate_limited"
    assert lease is None


class ZeroInsertDB(FakeDB):
    def prepare(self, query):
        statement = super().prepare(query)
        if query.lstrip().startswith("INSERT OR IGNORE INTO public_admission_events"):
            statement.run = self._zero_insert
        return statement

    async def _zero_insert(self):
        return {"meta": {"changes": 0}}


@pytest.mark.asyncio
async def test_d1_store_fails_closed_when_insert_races():
    store = D1AdmissionStore(ZeroInsertDB())
    decision, lease = await store.acquire(
        subject_fingerprint="subject-1",
        route=AdmissionRoute.RESEARCH,
        policy=AdmissionPolicy(),
        event_id="event-1",
        now=120,
    )
    assert decision.allowed is False
    assert decision.outcome.value == "concurrency_limited"
    assert lease is None


@pytest.mark.asyncio
async def test_d1_store_rejects_empty_identity_fields():
    store = D1AdmissionStore(FakeDB())
    with pytest.raises(ValueError, match="subject_fingerprint is required"):
        await store.acquire(
            subject_fingerprint="",
            route=AdmissionRoute.RESEARCH,
            policy=AdmissionPolicy(),
            event_id="event-1",
            now=120,
        )
    with pytest.raises(ValueError, match="event_id is required"):
        await store.acquire(
            subject_fingerprint="subject-1",
            route=AdmissionRoute.RESEARCH,
            policy=AdmissionPolicy(),
            event_id="",
            now=120,
        )


@pytest.mark.asyncio
async def test_d1_store_release_none_is_noop():
    db = FakeDB()
    await D1AdmissionStore(db).release(None)
    assert db.queries == []


def test_admission_response_without_retry_after_header():
    import worker
    from backend.admission import AdmissionDecision, AdmissionOutcome

    response = worker._admission_response(
        AdmissionDecision(
            AdmissionOutcome.RATE_LIMITED,
            AdmissionRoute.RESEARCH,
            False,
            "rate limited",
            retry_after_seconds=0,
        )
    )
    assert response.status == 429
    assert "Retry-After" not in response.headers


@pytest.mark.asyncio
async def test_worker_research_success_missing_lease_runs_through_finally(monkeypatch):
    import worker

    async def admit(*args, **kwargs):
        return accepted_admission(None)

    class FullPersistence(Persistence):
        def __init__(self):
            super().__init__()
            self.statuses = []

        async def set_run_status(self, run_id, status):
            self.statuses.append((run_id, status))

    persistence = FullPersistence()
    monkeypatch.setattr(worker, "_public_admit", admit)
    monkeypatch.setattr(
        worker,
        "submit_research",
        lambda request: type(
            "Result",
            (),
            {"ok": True, "run_id": "run-full", "metadata": {"mode": "test"}},
        )(),
    )
    monkeypatch.setattr(worker, "CloudflarePersistence", lambda env: persistence)

    async def ingest(*args, **kwargs):
        return []

    monkeypatch.setattr(worker, "_ingest_sources", ingest)

    env = type("Env", (), {"AUTH_TOKEN": "secret", "DB": object()})()
    entry = worker.Default()
    entry.env = env
    response = await entry.fetch(
        Request(
            "POST",
            "https://x/api/v1/research",
            {
                "question": "q",
                "source_urls": ["https://example.com"],
                "strict_zero_cost_only": True,
            },
            {"Authorization": "Bearer secret", "Content-Type": "application/json"},
        )
    )
    assert response.status == 200
    assert persistence.created == ["run-full"]
    assert persistence.statuses == [("run-full", "running"), ("run-full", "completed")]



class IdempotentAdmissionDB(FakeDB):
    def __init__(self):
        super().__init__()
        self.events = {}
        self.reclaim_changes = 1

    def prepare(self, query):
        db = self

        class StatefulStatement(FakeStatement):
            async def run(self_inner):
                sql = self_inner.query.lower().strip()
                args = self_inner.args

                if sql.startswith("delete from public_admission_events"):
                    return {"meta": {"changes": 0}}

                if sql.startswith("insert or ignore into public_admission_events"):
                    event_id, window_start, subject, route, cost_units, expires_at = args[:6]
                    if event_id in db.events:
                        return {"meta": {"changes": 0}}
                    db.events[event_id] = {
                        "event_id": event_id,
                        "window_start": window_start,
                        "subject_fingerprint": subject,
                        "route": route,
                        "cost_units": cost_units,
                        "lease_expires_at": expires_at,
                        "released_at": None,
                    }
                    return {"meta": {"changes": 1}}

                if sql.startswith("update public_admission_events set released_at"):
                    released_at, event_id = args
                    row = db.events.get(event_id)
                    if row and row["released_at"] is None:
                        row["released_at"] = released_at
                        return {"meta": {"changes": 1}}
                    return {"meta": {"changes": 0}}

                if sql.startswith("update public_admission_events set window_start"):
                    if db.reclaim_changes == 0:
                        return {"meta": {"changes": 0}}
                    window_start, expires_at, event_id, subject, route, now = args
                    row = db.events.get(event_id)
                    if (
                        row
                        and row["subject_fingerprint"] == subject
                        and row["route"] == route
                        and row["released_at"] is None
                        and row["lease_expires_at"] <= now
                    ):
                        row.update(window_start=window_start, lease_expires_at=expires_at)
                        return {"meta": {"changes": 1}}
                    return {"meta": {"changes": 0}}

                if sql.startswith("select event_id"):
                    row = db.events.get(args[0])
                    return {"results": [row] if row else []}

                return {"meta": {"changes": 1}}

            async def first(self_inner):
                sql = self_inner.query.lower().strip()
                if sql.startswith("select event_id"):
                    row = db.events.get(self_inner.args[0])
                    return row
                return {
                    "subject_requests": len(db.events),
                    "global_requests": len(db.events),
                    "subject_concurrent": sum(
                        1 for row in db.events.values()
                        if row["released_at"] is None
                    ),
                    "global_concurrent": sum(
                        1 for row in db.events.values()
                        if row["released_at"] is None
                    ),
                }

        return StatefulStatement(query)


def test_d1_store_replays_same_event_without_a_second_admission_slot():
    import asyncio

    db = IdempotentAdmissionDB()
    store = D1AdmissionStore(db)
    policy = AdmissionPolicy()

    first_decision, first_lease = asyncio.run(
        store.acquire(
            subject_fingerprint="subject-1",
            route=AdmissionRoute.CHAT,
            policy=policy,
            event_id="replay-key",
            now=120,
        )
    )
    assert first_decision.allowed is True
    assert first_lease is not None
    asyncio.run(store.release(first_lease))

    second_decision, second_lease = asyncio.run(
        store.acquire(
            subject_fingerprint="subject-1",
            route=AdmissionRoute.CHAT,
            policy=policy,
            event_id="replay-key",
            now=121,
        )
    )
    assert second_decision.allowed is True
    assert second_lease is None


def test_d1_store_rejects_replay_across_admission_scopes():
    import asyncio

    db = IdempotentAdmissionDB()
    db.events["scope-key"] = {
        "event_id": "scope-key",
        "window_start": 120,
        "subject_fingerprint": "other-subject",
        "route": "chat",
        "cost_units": 2,
        "lease_expires_at": 180,
        "released_at": 150,
    }
    decision, lease = asyncio.run(
        D1AdmissionStore(db).acquire(
            subject_fingerprint="subject-1",
            route=AdmissionRoute.CHAT,
            policy=AdmissionPolicy(),
            event_id="scope-key",
            now=121,
        )
    )
    assert decision.outcome.value == "duplicate"
    assert decision.allowed is False
    assert lease is None


def test_d1_store_reclaims_expired_admission_lease():
    import asyncio

    db = IdempotentAdmissionDB()
    store = D1AdmissionStore(db)
    first_decision, first_lease = asyncio.run(
        store.acquire(
            subject_fingerprint="subject-1",
            route=AdmissionRoute.CHAT,
            policy=AdmissionPolicy(),
            event_id="expired-key",
            now=120,
        )
    )
    assert first_decision.allowed is True
    assert first_lease is not None
    db.events["expired-key"]["lease_expires_at"] = 0

    decision, lease = asyncio.run(
        store.acquire(
            subject_fingerprint="subject-1",
            route=AdmissionRoute.CHAT,
            policy=AdmissionPolicy(),
            event_id="expired-key",
            now=121,
        )
    )
    assert decision.allowed is True
    assert lease is not None
    assert lease.expires_at == 181


def test_d1_store_keeps_released_non_idempotent_duplicate_on_admission_decision():
    import asyncio

    db = IdempotentAdmissionDB()
    db.events["cheap-key"] = {
        "event_id": "cheap-key",
        "window_start": 120,
        "subject_fingerprint": "subject-1",
        "route": "cheap_read",
        "cost_units": 1,
        "lease_expires_at": 180,
        "released_at": 150,
    }
    decision, lease = asyncio.run(
        D1AdmissionStore(db).acquire(
            subject_fingerprint="subject-1",
            route=AdmissionRoute.CHEAP_READ,
            policy=AdmissionPolicy(),
            event_id="cheap-key",
            now=121,
        )
    )
    assert decision.allowed is True
    assert lease is None


def test_d1_store_blocks_active_non_idempotent_duplicate():
    import asyncio

    db = IdempotentAdmissionDB()
    store = D1AdmissionStore(db)
    first_decision, first_lease = asyncio.run(
        store.acquire(
            subject_fingerprint="subject-1",
            route=AdmissionRoute.CHEAP_READ,
            policy=AdmissionPolicy(),
            event_id="cheap-active-key",
            now=120,
        )
    )
    assert first_decision.allowed is True
    assert first_lease is not None

    decision, lease = asyncio.run(
        store.acquire(
            subject_fingerprint="subject-1",
            route=AdmissionRoute.CHEAP_READ,
            policy=AdmissionPolicy(),
            event_id="cheap-active-key",
            now=121,
        )
    )
    assert decision.outcome.value == "concurrency_limited"
    assert decision.allowed is False
    assert lease is None


def test_d1_store_delegates_active_chat_duplicate_to_idempotency_authority():
    import asyncio

    db = IdempotentAdmissionDB()
    store = D1AdmissionStore(db)
    first_decision, first_lease = asyncio.run(
        store.acquire(
            subject_fingerprint="subject-1",
            route=AdmissionRoute.CHAT,
            policy=AdmissionPolicy(),
            event_id="active-key",
            now=120,
        )
    )
    assert first_decision.allowed is True
    assert first_lease is not None

    decision, lease = asyncio.run(
        store.acquire(
            subject_fingerprint="subject-1",
            route=AdmissionRoute.CHAT,
            policy=AdmissionPolicy(),
            event_id="active-key",
            now=121,
        )
    )
    assert decision.outcome.value == "accepted"
    assert decision.allowed is True
    assert lease is None


def test_d1_store_delegates_active_stream_duplicate_to_idempotency_authority():
    import asyncio

    db = IdempotentAdmissionDB()
    store = D1AdmissionStore(db)
    first_decision, first_lease = asyncio.run(
        store.acquire(
            subject_fingerprint="subject-1",
            route=AdmissionRoute.STREAM,
            policy=AdmissionPolicy(),
            event_id="active-stream-key",
            now=120,
        )
    )
    assert first_decision.allowed is True
    assert first_lease is not None

    decision, lease = asyncio.run(
        store.acquire(
            subject_fingerprint="subject-1",
            route=AdmissionRoute.STREAM,
            policy=AdmissionPolicy(),
            event_id="active-stream-key",
            now=121,
        )
    )
    assert decision.outcome.value == "accepted"
    assert decision.allowed is True
    assert lease is None


def test_d1_store_delegates_active_research_duplicate_to_idempotency_authority():
    import asyncio

    db = IdempotentAdmissionDB()
    store = D1AdmissionStore(db)
    first_decision, first_lease = asyncio.run(
        store.acquire(
            subject_fingerprint="subject-1",
            route=AdmissionRoute.RESEARCH,
            policy=AdmissionPolicy(),
            event_id="active-research-key",
            now=120,
        )
    )
    assert first_decision.allowed is True
    assert first_lease is not None

    decision, lease = asyncio.run(
        store.acquire(
            subject_fingerprint="subject-1",
            route=AdmissionRoute.RESEARCH,
            policy=AdmissionPolicy(),
            event_id="active-research-key",
            now=121,
        )
    )
    assert decision.outcome.value == "accepted"
    assert decision.allowed is True
    assert lease is None


def test_d1_store_delegates_chat_after_failed_lease_reclaim_race():
    import asyncio

    db = IdempotentAdmissionDB()
    store = D1AdmissionStore(db)
    first_decision, first_lease = asyncio.run(
        store.acquire(
            subject_fingerprint="subject-1",
            route=AdmissionRoute.CHAT,
            policy=AdmissionPolicy(),
            event_id="reclaim-race-key",
            now=120,
        )
    )
    assert first_decision.allowed is True
    assert first_lease is not None
    db.events["reclaim-race-key"]["lease_expires_at"] = 0
    db.reclaim_changes = 0

    decision, lease = asyncio.run(
        store.acquire(
            subject_fingerprint="subject-1",
            route=AdmissionRoute.CHAT,
            policy=AdmissionPolicy(),
            event_id="reclaim-race-key",
            now=121,
        )
    )
    assert decision.outcome.value == "accepted"
    assert decision.allowed is True
    assert lease is None
