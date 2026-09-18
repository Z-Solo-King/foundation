import asyncio
from types import SimpleNamespace

import pytest

from backend.public_read_cursor import encode_cursor
from backend.worker_research import get_run


class Statement:
    def __init__(self, sql, first_value=None, rows=None):
        self.sql = sql
        self.first_value = first_value
        self.rows = rows if rows is not None else []

    def bind(self, *args):
        self.args = args
        return self

    async def first(self):
        if "FROM research_runs" in getattr(self, "sql", "") and self.args and len(self.args) >= 2:
            if self.first_value is not None and self.args[1] != SECRET:
                return None
        return self.first_value

    async def all(self):
        if not self.rows:
            return []
        offset = self.args[-1] if len(getattr(self, "args", ())) >= 2 else 0
        limit = self.args[-2] if len(getattr(self, "args", ())) >= 2 else len(self.rows)
        return self.rows[offset:offset + limit]


class DB:
    def __init__(self, run, rows):
        self.run = run
        self.rows = rows
        self.statements = []

    def prepare(self, sql):
        statement = Statement(
            sql,
            self.run if "FROM research_runs" in sql else None,
            self.rows if "FROM observations" in sql else [],
        )
        self.statements.append(statement)
        return statement


SECRET = "subject-1"
RUN = {
    "run_id": "run-1",
    "status": "completed",
    "created_at": "2026-09-18T03:00:00+00:00",
    "updated_at": "2026-09-18T03:10:00+00:00",
    "depth": "standard",
    "require_citations": 1,
    "max_sources": 20,
    "max_evidence_items": 100,
}


def rows(count):
    return [
        {
            "observation_id": f"o{i}",
            "source_id": f"s{i}",
            "version_id": f"v{i}",
            "observed_at": f"2026-09-18T03:{i:02d}:00+00:00",
            "retrieval_method": "http_fetch",
            "content_hash": f"h{i}",
            "integrity_state": "verified",
            "access_state": "accessible",
            "url": f"https://example.test/{i}",
            "source_family_id": "example.test",
        }
        for i in range(count)
    ]


def test_public_run_read_is_subject_bound_and_paginated():
    env = SimpleNamespace(DB=DB(RUN, rows(3)))
    first = asyncio.run(get_run(env, "run-1", subject_fingerprint=SECRET, limit=2, cursor_secret=SECRET))
    assert first["run"]["run_id"] == "run-1"
    assert len(first["observations"]) == 2
    assert first["pagination"]["has_more"] is True
    assert first["pagination"]["next_cursor"]

    second = asyncio.run(
        get_run(
            env,
            "run-1",
            subject_fingerprint=SECRET,
            limit=2,
            cursor=first["pagination"]["next_cursor"],
            cursor_secret=SECRET,
        )
    )
    assert [row["observation_id"] for row in second["observations"]] == ["o2"]
    assert second["pagination"]["has_more"] is False


def test_public_run_read_rejects_wrong_subject_and_invalid_page_size():
    env = SimpleNamespace(DB=DB(RUN, rows(1)))
    assert asyncio.run(get_run(env, "run-1", subject_fingerprint="wrong", limit=1, cursor_secret=SECRET)) is None
    with pytest.raises(ValueError):
        asyncio.run(get_run(env, "run-1", subject_fingerprint=SECRET, limit=0, cursor_secret=SECRET))
    with pytest.raises(ValueError):
        asyncio.run(get_run(env, "run-1", subject_fingerprint="", limit=1, cursor_secret=SECRET))


def test_public_run_read_handles_missing_runs_and_stale_cursor():
    env = SimpleNamespace(DB=DB(None, rows(1)))
    assert asyncio.run(get_run(env, "missing", subject_fingerprint=SECRET, limit=1, cursor_secret=SECRET)) is None
    env = SimpleNamespace(DB=DB(RUN, rows(1)))
    cursor = encode_cursor(
        secret=SECRET,
        subject_fingerprint=SECRET,
        run_id="run-1",
        snapshot_id="old-snapshot",
        offset=0,
        expires_at=2_000_000_000,
    )
    with pytest.raises(ValueError, match="snapshot"):
        asyncio.run(get_run(env, "run-1", subject_fingerprint=SECRET, limit=1, cursor=cursor, cursor_secret=SECRET))


def test_row_value_supports_mapping_and_object_rows():
    from backend.worker_research import _row_value
    row = SimpleNamespace(status="completed")
    assert _row_value(row, "status") == "completed"
    assert _row_value(row, "missing", "fallback") == "fallback"
