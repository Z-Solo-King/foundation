CREATE TABLE IF NOT EXISTS research_runs (
    run_id TEXT PRIMARY KEY,
    question TEXT NOT NULL,
    depth TEXT NOT NULL CHECK (depth IN ('quick','standard','deep')),
    require_citations INTEGER NOT NULL CHECK (require_citations IN (0,1)),
    max_sources INTEGER NOT NULL CHECK (max_sources > 0),
    max_evidence_items INTEGER NOT NULL CHECK (max_evidence_items > 0),
    strict_zero_cost_only INTEGER NOT NULL CHECK (strict_zero_cost_only IN (0,1)),
    status TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_research_runs_status ON research_runs(status);
CREATE INDEX IF NOT EXISTS idx_research_runs_created_at ON research_runs(created_at);
