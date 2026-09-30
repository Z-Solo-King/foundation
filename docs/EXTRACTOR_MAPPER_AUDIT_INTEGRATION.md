# Extractor / Mapper Audit Integration

Foundation automation consumes the private Operations extractor-surface audit as evidence metadata. It does not import private runtime or become a second extractor authority.

Canonical chain:
`Operations extractor_mapper capability registry` -> `policy/evidence/migration crosswalk` -> `Git-history oldest-surface report` -> `Foundation CI artifact`.

The workflow uses the existing read-only GitHub App credential pair already used for cross-repository Operations access. It adds no new credential requirement.

Operations has no separate GitHub Actions authority. Foundation remains the automation/release owner; Operations remains the private runtime/governance owner.

## 2026-09-30 verification repair
Operations #1388 corrected the Git-history parser used by the extractor governance bridge. The bridge must run against the live Operations main and keep the resulting report as CI evidence rather than treating the parser or report as runtime authority.


## 2026-09-30 live synchronization reconciliation

Foundation/Operations state was re-read from GitHub before this synchronization update.

- Foundation main: `bda977551bb54bb912046b76bf72b6a98ac49bf5`.
- Operations main: `b2f6b9d092a50d46c601bf31f52e012e6b5023a2`.
- Certified production Operations revision: `d0897d13751a092cc68ec7a0479a9000e18cff7d`.
- Foundation non-feed open issues: #58, #157.
- Operations open issues: #597, #603.
- Current non-feed implementation PRs: Foundation #1606 and Operations #1400.
- Foundation #1575 was merged after current-head validation.

This document is synchronization/navigation metadata only. Runtime, deployment, promotion and rollback authority remain with their canonical live evidence surfaces.
