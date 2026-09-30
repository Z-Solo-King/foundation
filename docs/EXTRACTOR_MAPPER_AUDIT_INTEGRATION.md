# Extractor / Mapper Audit Integration

Foundation automation consumes the private Operations extractor-surface audit as evidence metadata. It does not import private runtime or become a second extractor authority.

Canonical chain:
`Operations extractor_mapper capability registry` -> `policy/evidence/migration crosswalk` -> `Git-history oldest-surface report` -> `Foundation CI artifact`.

The workflow uses the existing read-only GitHub App credential pair already used for cross-repository Operations access. It adds no new credential requirement.

Operations has no separate GitHub Actions authority. Foundation remains the automation/release owner; Operations remains the private runtime/governance owner.

## 2026-09-30 verification repair
Operations #1388 corrected the Git-history parser used by the extractor governance bridge. The bridge must run against the live Operations main and keep the resulting report as CI evidence rather than treating the parser or report as runtime authority.
