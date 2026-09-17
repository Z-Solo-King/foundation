CREATE TABLE IF NOT EXISTS research_publication_history (
    run_id TEXT NOT NULL REFERENCES research_runs(run_id),
    package_digest TEXT NOT NULL,
    package_json TEXT NOT NULL,
    published_at TEXT NOT NULL,
    superseded_at TEXT NOT NULL,
    PRIMARY KEY (run_id, package_digest)
);
CREATE INDEX IF NOT EXISTS idx_research_publication_history_run_published_at
    ON research_publication_history(run_id, published_at);
