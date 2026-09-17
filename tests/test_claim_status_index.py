from __future__ import annotations

import sqlite3
from pathlib import Path


def test_claim_status_index_is_present_and_used_for_status_filter():
    connection = sqlite3.connect(":memory:")
    connection.execute(
        """CREATE TABLE claims (
            claim_id TEXT PRIMARY KEY,
            run_id TEXT NOT NULL,
            text TEXT NOT NULL,
            status TEXT NOT NULL,
            confidence REAL,
            valid_from TEXT,
            valid_until TEXT,
            created_at TEXT NOT NULL
        )"""
    )
    connection.executemany(
        "INSERT INTO claims(claim_id, run_id, text, status, valid_from, created_at) VALUES (?, ?, ?, ?, ?, ?)",
        [(f"c{i}", "r1", f"claim {i}", "active" if i % 2 else "retracted", f"2026-01-{(i % 28) + 1:02d}", "2026-01-01") for i in range(200)],
    )
    migration = Path("migrations/0008_claim_status_index.sql").read_text(encoding="utf-8")
    connection.executescript(migration)

    index_columns = connection.execute("PRAGMA index_info('idx_claims_status')").fetchall()
    assert [row[2] for row in index_columns] == ["status", "valid_from"]

    plan = connection.execute(
        "EXPLAIN QUERY PLAN SELECT claim_id FROM claims WHERE status = ? AND valid_from <= ?",
        ("active", "2026-12-31"),
    ).fetchall()
    detail = " ".join(row[3] for row in plan)
    assert "idx_claims_status" in detail
