CREATE TABLE IF NOT EXISTS sources (
    source_id TEXT PRIMARY KEY,
    url TEXT NOT NULL,
    source_family_id TEXT NOT NULL,
    origin_kind TEXT NOT NULL,
    first_observed_at TEXT,
    last_observed_at TEXT,
    access_state TEXT NOT NULL DEFAULT 'unknown'
);

CREATE TABLE IF NOT EXISTS source_lineage (
    source_id TEXT PRIMARY KEY REFERENCES sources(source_id),
    parent_source_id TEXT,
    derivation_type TEXT NOT NULL,
    lineage_hash TEXT,
    FOREIGN KEY (parent_source_id) REFERENCES sources(source_id)
);

CREATE TABLE IF NOT EXISTS document_versions (
    version_id TEXT PRIMARY KEY,
    source_id TEXT NOT NULL REFERENCES sources(source_id),
    retrieved_at TEXT NOT NULL,
    etag TEXT,
    content_hash TEXT NOT NULL,
    artifact_ref TEXT,
    content_length INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS observations (
    observation_id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL REFERENCES research_runs(run_id),
    source_id TEXT NOT NULL REFERENCES sources(source_id),
    version_id TEXT REFERENCES document_versions(version_id),
    observed_at TEXT NOT NULL,
    retrieval_method TEXT NOT NULL,
    content_hash TEXT,
    integrity_state TEXT NOT NULL DEFAULT 'unverified',
    access_state TEXT NOT NULL DEFAULT 'accessible'
);

CREATE TABLE IF NOT EXISTS evidence_spans (
    evidence_id TEXT PRIMARY KEY,
    observation_id TEXT NOT NULL REFERENCES observations(observation_id),
    span_start INTEGER NOT NULL CHECK (span_start >= 0),
    span_end INTEGER NOT NULL CHECK (span_end > span_start),
    span_hash TEXT NOT NULL,
    evidence_type TEXT NOT NULL DEFAULT 'direct',
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS claims (
    claim_id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL REFERENCES research_runs(run_id),
    text TEXT NOT NULL,
    status TEXT NOT NULL,
    confidence REAL,
    valid_from TEXT,
    valid_until TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS claim_evidence (
    claim_id TEXT NOT NULL REFERENCES claims(claim_id),
    evidence_id TEXT NOT NULL REFERENCES evidence_spans(evidence_id),
    relation TEXT NOT NULL DEFAULT 'supports',
    PRIMARY KEY (claim_id, evidence_id)
);

CREATE INDEX IF NOT EXISTS idx_sources_family ON sources(source_family_id);
CREATE INDEX IF NOT EXISTS idx_versions_source ON document_versions(source_id, retrieved_at);
CREATE INDEX IF NOT EXISTS idx_observations_run ON observations(run_id, observed_at);
CREATE INDEX IF NOT EXISTS idx_evidence_observation ON evidence_spans(observation_id);
CREATE INDEX IF NOT EXISTS idx_claims_run ON claims(run_id, created_at);
