-- Replace the run-keyed publication row with an append-only publication history.
-- The legacy table is retained for rollback/audit purposes; new writes use the
-- new publication identity and can never overwrite an earlier publication.
ALTER TABLE research_publications RENAME TO research_publications_legacy;

CREATE TABLE research_publications (
    publication_id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT NOT NULL REFERENCES research_runs(run_id),
    package_digest TEXT NOT NULL,
    package_json TEXT NOT NULL,
    published_at TEXT NOT NULL
);

INSERT INTO research_publications (run_id, package_digest, package_json, published_at)
SELECT run_id, package_digest, package_json, published_at
FROM research_publications_legacy
ORDER BY published_at, run_id;

CREATE INDEX idx_research_publications_run_id
    ON research_publications(run_id);
CREATE INDEX idx_research_publications_history_published_at
    ON research_publications(published_at);
