-- Reverse-traversal index gap identified in #442: claim -> validity
-- window/status was only covered for (valid_from, valid_until); lookups
-- filtering by claim status had no indexed access path and could fall back
-- to a full table scan.
CREATE INDEX IF NOT EXISTS idx_claims_status ON claims(status, valid_from);
