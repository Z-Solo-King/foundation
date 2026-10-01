from __future__ import annotations

import asyncio
import pytest


from backend.admission import AdmissionDecision, AdmissionOutcome, AdmissionPolicy, AdmissionRoute
from backend.admission_store import D1AdmissionStore, ROUTE_COST_UNITS, _insert_new_admission, _storage_event_id
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

class ZeroInsertDB(FakeDB):
    def prepare(self, query):
        statement = super().prepare(query)
        if query.lstrip().startswith("INSERT OR IGNORE INTO public_admission_events"):
            statement.run = self._zero_insert
        return statement

    async def _zero_insert(self):
        return {"meta": {"changes": 0}}


@pytest.mark.asyncio

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


