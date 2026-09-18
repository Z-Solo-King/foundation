ALTER TABLE research_runs ADD COLUMN subject_fingerprint TEXT NOT NULL DEFAULT 'legacy';

CREATE INDEX IF NOT EXISTS idx_research_runs_subject
    ON research_runs(subject_fingerprint, run_id);
