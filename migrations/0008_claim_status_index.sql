-- Reverse-traversal index gap identified in #442: "claim -> validity
-- window/status" was only covered for (valid_from, valid_until); lookups
-- filtering by claim status (e.g. active/retracted/superseded claims for
-- a run) had no indexed access path and fell back to a full table scan.
CREATE INDEX IF NOT EXISTS idx_claims_status ON claims(status, valid_from);
