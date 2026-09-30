# Extractor / Mapper Audit Integration

Foundation automation consumes the private Operations extractor-surface audit as evidence metadata. It does not import private runtime or become a second extractor authority.

Canonical chain:
`Operations extractor_mapper capability registry` -> `policy/evidence/migration crosswalk` -> `Git-history oldest-surface report` -> `Foundation CI artifact`.

The workflow uses the existing read-only GitHub App credential pair already used for cross-repository Operations access. It adds no new credential requirement.

Operations has no separate GitHub Actions authority. Foundation remains the automation/release owner; Operations remains the private runtime/governance owner.

## 2026-09-30 verification repair
Operations #1388 corrected the Git-history parser used by the extractor governance bridge. The bridge must run against the live Operations main and keep the resulting report as CI evidence rather than treating the parser or report as runtime authority.


## 2026-09-30 final synchronization
- Operations extractor governance PR #1395 (exact feature/function/policy coverage) merged; #1396 (delegated-owner and retained-capability enforcement) merged.
- Foundation bridge PR #1615 merged after rebasing onto current Foundation main and passing all 11 observed checks, including CodeQL, public tests, Python analysis, workflow-security regression, zizmor and Scorecard.
- Current live Operations main at the synchronization point: `c6cc64364b7d3bd3e536a8a847ee01357458fb31`.
- The former standalone extractor-mapper repository remains retired/deleted. `operations/extractor_mapper/` is the private runtime boundary; Foundation canonical deterministic mapper/data-quality primitives remain the semantic authority for delegated capabilities.
- Future synchronization must refresh live GitHub heads/issues/PRs before mutation. Dated maps and migration snapshots remain evidence, not mutable queue authority.
