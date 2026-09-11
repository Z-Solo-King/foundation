CREATE INDEX IF NOT EXISTS idx_observations_source ON observations(source_id, observed_at);
CREATE INDEX IF NOT EXISTS idx_observations_version ON observations(version_id, observed_at);
CREATE INDEX IF NOT EXISTS idx_observations_hash ON observations(content_hash);
CREATE INDEX IF NOT EXISTS idx_document_versions_hash ON document_versions(content_hash);
CREATE INDEX IF NOT EXISTS idx_source_lineage_parent ON source_lineage(parent_source_id);
CREATE INDEX IF NOT EXISTS idx_claims_validity ON claims(valid_from, valid_until);
CREATE INDEX IF NOT EXISTS idx_claim_evidence_evidence ON claim_evidence(evidence_id, claim_id);
CREATE INDEX IF NOT EXISTS idx_claim_evidence_relation ON claim_evidence(relation, claim_id);
CREATE INDEX IF NOT EXISTS idx_sources_origin_family ON sources(source_family_id, source_id);
