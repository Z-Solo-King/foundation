CREATE TABLE IF NOT EXISTS public_admission_events (
    event_id TEXT PRIMARY KEY,
    window_start INTEGER NOT NULL,
    subject_fingerprint TEXT NOT NULL,
    route TEXT NOT NULL,
    cost_units INTEGER NOT NULL CHECK (cost_units > 0),
    lease_expires_at INTEGER NOT NULL,
    released_at INTEGER
);

CREATE INDEX IF NOT EXISTS idx_public_admission_window
    ON public_admission_events(window_start, subject_fingerprint);

CREATE INDEX IF NOT EXISTS idx_public_admission_leases
    ON public_admission_events(subject_fingerprint, lease_expires_at, released_at);
