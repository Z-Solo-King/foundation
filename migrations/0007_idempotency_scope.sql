ALTER TABLE idempotency_keys ADD COLUMN subject_fingerprint TEXT NOT NULL DEFAULT 'legacy';
ALTER TABLE idempotency_keys ADD COLUMN capability TEXT NOT NULL DEFAULT 'research';
ALTER TABLE idempotency_keys ADD COLUMN contract_revision TEXT NOT NULL DEFAULT 'v1';

CREATE INDEX IF NOT EXISTS idx_idempotency_scope
    ON idempotency_keys(subject_fingerprint, capability, contract_revision);