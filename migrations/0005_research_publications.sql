CREATE TABLE IF NOT EXISTS research_publications (
    run_id TEXT PRIMARY KEY REFERENCES research_runs(run_id),
    package_digest TEXT NOT NULL,
    package_json TEXT NOT NULL,
    published_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_research_publications_published_at ON research_publications(published_at);
