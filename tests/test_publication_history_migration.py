from pathlib import Path
import sqlite3


def test_publication_history_migration_preserves_previous_versions():
    root = Path(__file__).resolve().parents[1]
    migration = (root / "migrations" / "0006_research_publication_history.sql").read_text(encoding="utf-8")

    connection = sqlite3.connect(":memory:")
    connection.executescript(
        """
        PRAGMA foreign_keys = ON;
        CREATE TABLE research_runs (run_id TEXT PRIMARY KEY);
        CREATE TABLE research_publications (
            run_id TEXT PRIMARY KEY REFERENCES research_runs(run_id),
            package_digest TEXT NOT NULL,
            package_json TEXT NOT NULL,
            published_at TEXT NOT NULL
        );
        INSERT INTO research_runs(run_id) VALUES ('run-1');
        INSERT INTO research_publications VALUES ('run-1', 'digest-1', '{\"answer\":1}', '2026-09-17T10:00:00Z');
        """
    )
    connection.executescript(migration)

    seeded = connection.execute(
        "SELECT run_id, package_digest, package_json, published_at FROM research_publication_history"
    ).fetchall()
    assert seeded == [("run-1", "digest-1", '{"answer":1}', "2026-09-17T10:00:00Z")]

    connection.execute(
        """
        UPDATE research_publications
        SET package_digest = ?, package_json = ?, published_at = ?
        WHERE run_id = ?
        """,
        ("digest-2", '{"answer":2}', "2026-09-17T11:00:00Z", "run-1"),
    )

    history = connection.execute(
        """
        SELECT run_id, package_digest, package_json, published_at
        FROM research_publication_history
        ORDER BY published_at
        """
    ).fetchall()
    assert history == [
        ("run-1", "digest-1", '{"answer":1}', "2026-09-17T10:00:00Z"),
    ]

    current = connection.execute(
        "SELECT package_digest, package_json, published_at FROM research_publications WHERE run_id = ?",
        ("run-1",),
    ).fetchone()
    assert current == ("digest-2", '{"answer":2}', "2026-09-17T11:00:00Z")
